"""tests/test_machine_submissions.py — Suíte de testes da Esteira de Submissão, Análise e Publicação de Máquinas."""
import os
import io
import json
import zipfile
import tempfile
import sqlite3
import unittest
from pathlib import Path

from modules.machine_submissions.db import init_submissions_db, log_machine_audit
from modules.machine_submissions.state_machine import (
    transition_submission,
    can_transition,
    StateTransitionError,
    ALLOWED_TRANSITIONS
)
from modules.machine_submissions.validator import (
    extract_package,
    validate_extracted_structure,
    ValidationError
)
from modules.machine_submissions.scanner import (
    scan_dockerfile,
    scan_compose,
    scan_file_for_secrets,
    run_full_security_scan
)
from modules.machine_submissions.worker import (
    run_build_job,
    run_scan_job,
    run_test_job
)


def create_sample_zip(extra_files=None, zipslip=False):
    """Cria buffer ZIP em memória para testes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        manifest_content = """machine:
  name: "Test Lab Box"
  version: "1.0"
metadata:
  difficulty: "medium"
  os: "linux"
  category: "web"
  short_description: "Laboratório de teste automatizado"
  author:
    name: "CyberLab"
    url: "https://duno.lab"
runtime:
  ports:
    - 80
flags:
  - type: "user"
    value: "DUNO{user_flag_123}"
    points: 100
  - type: "root"
    value: "DUNO{root_flag_999}"
    points: 200
"""
        zf.writestr("manifest.yml", manifest_content)
        zf.writestr("Dockerfile", "FROM alpine:3.18\nRUN echo hello\nEXPOSE 80\n")
        zf.writestr("README.md", "# Test Lab Box\n\nWriteup e solução do desafio.\n")

        if extra_files:
            for fname, fcontent in extra_files.items():
                zf.writestr(fname, fcontent)

        if zipslip:
            zf.writestr("../../evil.txt", "payload")

    buf.seek(0)
    return buf


class TestValidatorAndExtraction(unittest.TestCase):
    """Testes de integridade, descompactação segura e schema de manifesto."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.dest_dir = Path(self.tmp_dir.name) / "extracted"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_safe_zip_extraction(self):
        """ZIP válido deve ser extraído e indexado com hash sha256."""
        zip_buf = create_sample_zip()
        zip_file = Path(self.tmp_dir.name) / "sample.zip"
        zip_file.write_bytes(zip_buf.getvalue())

        files = extract_package(str(zip_file), str(self.dest_dir))
        self.assertTrue(len(files) >= 3)
        paths = [f["file_path"] for f in files]
        self.assertIn("manifest.yml", paths)
        self.assertIn("Dockerfile", paths)
        self.assertIn("README.md", paths)
        self.assertTrue(all(len(f["sha256"]) == 64 for f in files))

        # Validação estrutural
        manifest = validate_extracted_structure(str(self.dest_dir))
        self.assertEqual(manifest["machine"]["name"], "Test Lab Box")
        self.assertEqual(manifest["metadata"]["difficulty"], "medium")

    def test_zipslip_traversal_raises_validation_error(self):
        """Arquivo com caminho malicioso '../../evil.txt' deve ser bloqueado com ValidationError."""
        zip_buf = create_sample_zip(zipslip=True)
        zip_file = Path(self.tmp_dir.name) / "evil.zip"
        zip_file.write_bytes(zip_buf.getvalue())

        with self.assertRaises(ValidationError) as ctx:
            extract_package(str(zip_file), str(self.dest_dir))
        self.assertIn("Path Traversal", str(ctx.exception))

    def test_invalid_magic_bytes_rejected(self):
        """Arquivo com extensão .zip mas cabeçalho não-zip deve ser rejeitado."""
        fake_zip = Path(self.tmp_dir.name) / "fake.zip"
        fake_zip.write_bytes(b"MZ\x90\x00\x03\x00\x00\x00Executable file pretending to be zip")

        with self.assertRaises(ValidationError) as ctx:
            extract_package(str(fake_zip), str(self.dest_dir))
        self.assertIn("magic bytes", str(ctx.exception).lower())

    def test_zip_symlink_rejected(self):
        """Arquivo ZIP contendo symlink POSIX deve ser bloqueado com ValidationError."""
        zip_file = Path(self.tmp_dir.name) / "symlink.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("manifest.yml", "machine: {name: 'Sym'}\nmetadata: {}\nruntime: {}\n")
            zf.writestr("Dockerfile", "FROM alpine\n")
            info = zipfile.ZipInfo("bad_link")
            info.create_system = 3
            info.external_attr = (0o120777 << 16)
            zf.writestr(info, "/etc/shadow")

        with self.assertRaises(ValidationError) as ctx:
            extract_package(str(zip_file), str(self.dest_dir))
        self.assertIn("Links simbólicos", str(ctx.exception))

    def test_tar_symlink_rejected(self):
        """Arquivo TAR contendo link simbólico deve ser bloqueado com ValidationError."""
        import tarfile
        tar_file = Path(self.tmp_dir.name) / "symlink.tar.gz"
        with tarfile.open(tar_file, "w:gz") as tf:
            ti = tarfile.TarInfo("bad_link")
            ti.type = tarfile.SYMTYPE
            ti.linkname = "/etc/passwd"
            tf.addfile(ti)

        with self.assertRaises(ValidationError) as ctx:
            extract_package(str(tar_file), str(self.dest_dir))
        self.assertIn("Links simbólicos", str(ctx.exception))

    def test_validate_extracted_structure_missing_required_section(self):
        """Manifesto sem seções obrigatórias deve levantar ValidationError."""
        dest = Path(self.tmp_dir.name) / "incomplete_box"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "manifest.yml").write_text("machine:\n  name: 'Incomplete'\n")
        (dest / "Dockerfile").write_text("FROM alpine\n")
        (dest / "README.md").write_text("# Doc\n")

        with self.assertRaises(ValidationError) as ctx:
            validate_extracted_structure(str(dest))
        self.assertIn("Seção obrigatória", str(ctx.exception))

    def test_validate_extracted_structure_missing_entrypoint(self):
        """Pacote sem Dockerfile ou docker-compose deve falhar na estrutura."""
        dest = Path(self.tmp_dir.name) / "empty_box"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "manifest.yml").write_text("machine:\n  name: Box\nmetadata: {}\nruntime: {}\n")
        (dest / "README.md").write_text("# Doc")

        with self.assertRaises(ValidationError) as ctx:
            validate_extracted_structure(str(dest))
        self.assertIn("Dockerfile", str(ctx.exception))


class TestSecurityScanner(unittest.TestCase):
    """Testes de análise estática de Dockerfile e Secrets Scanner."""

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_dockerfile_critical_findings(self):
        """Dockerfile com privileged, docker.sock mount ou host network deve gerar findings."""
        dockerfile_bad = Path(self.tmp_dir.name) / "Dockerfile"
        dockerfile_bad.write_text("""FROM ubuntu:22.04
RUN apt-get update
VOLUME /var/run/docker.sock
CMD ["/bin/bash"]
""")
        findings = scan_dockerfile(dockerfile_bad, "Dockerfile")
        categories = [f["category"] for f in findings]
        self.assertIn("docker_socket", categories)

    def test_secrets_scanner_detects_credentials(self):
        """Secrets scanner deve identificar chaves AWS, RSA e tokens."""
        fpath = Path(self.tmp_dir.name) / "config.py"
        fpath.write_text("""
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
GITHUB_TOKEN = "ghp_123456789012345678901234567890123456"
""")
        findings = scan_file_for_secrets(fpath, "config.py")
        descriptions = [f["description"] for f in findings]
        self.assertTrue(any("AWS Access Key" in d for d in descriptions))
        self.assertTrue(any("GitHub Token" in d for d in descriptions))


class TestStateMachineAndDatabase(unittest.TestCase):
    """Testes de ciclo de vida, persistência e auditoria."""

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp_db.name
        self.tmp_db.close()

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        );
        INSERT INTO users (id, username, password_hash, role) VALUES (1, 'alice', 'hash', 'user');
        INSERT INTO users (id, username, password_hash, role) VALUES (2, 'bob_admin', 'hash', 'admin');
        """)
        init_submissions_db(self.conn)

    def tearDown(self):
        self.conn.close()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_state_machine_valid_full_lifecycle(self):
        """Transição completa do DRAFT até PUBLISHED deve ter sucesso e registrar histórico."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO machine_submissions (user_id, slug, name, status) VALUES (1, 'box-1', 'Box 1', 'DRAFT')"
        )
        sub_id = cur.lastrowid
        self.conn.commit()

        # Sequência padrão
        steps = [
            ("SUBMITTED", "Submissão pelo autor"),
            ("TRIAGE", "Triagem pelo admin"),
            ("BUILDING", "Iniciando build"),
            ("SECURITY_REVIEW", "Iniciando scan"),
            ("FUNCTIONAL_TEST", "Iniciando testes"),
            ("CONTENT_REVIEW", "Revisão didática"),
            ("APPROVED", "Aprovado"),
            ("PUBLISHED", "Publicado")
        ]

        for to_state, reason in steps:
            transition_submission(self.conn, sub_id, to_state, changed_by_user_id=2, reason=reason)
            row = self.conn.execute("SELECT status FROM machine_submissions WHERE id = ?", (sub_id,)).fetchone()
            self.assertEqual(row["status"], to_state)

        # Histórico deve ter 8 registros
        history = self.conn.execute("SELECT * FROM machine_status_history WHERE submission_id = ?", (sub_id,)).fetchall()
        self.assertEqual(len(history), 8)

        # Auditoria deve registrar transições
        audit = self.conn.execute("SELECT * FROM machine_audit_logs WHERE resource_id = ?", (str(sub_id),)).fetchall()
        self.assertTrue(len(audit) >= 8)

    def test_state_machine_invalid_transition_raises_error(self):
        """Transição ilegal DRAFT -> PUBLISHED deve levantar StateTransitionError."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO machine_submissions (user_id, slug, name, status) VALUES (1, 'box-illegal', 'Box Illegal', 'DRAFT')"
        )
        sub_id = cur.lastrowid
        self.conn.commit()

        with self.assertRaises(StateTransitionError):
            transition_submission(self.conn, sub_id, "PUBLISHED", changed_by_user_id=2)


class TestFullAppRoutesIntegration(unittest.TestCase):
    """Testes de ponta a ponta nas rotas HTTP do usuário e do administrador."""

    @classmethod
    def setUpClass(cls):
        cls.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.tmp_db.name
        cls.tmp_db.close()
        os.environ["DATABASE"] = cls.db_path

        conn = sqlite3.connect(cls.db_path)
        conn.executescript("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE security_levels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            module TEXT NOT NULL,
            level TEXT NOT NULL,
            UNIQUE(user_id, module)
        );
        INSERT INTO users (id, username, password_hash, role) VALUES (1, 'author_user', 'hash', 'user');
        INSERT INTO users (id, username, password_hash, role) VALUES (2, 'admin_master', 'hash', 'admin');
        """)
        init_submissions_db(conn)
        conn.close()

        from app import create_app
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["DATABASE"] = cls.db_path

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def setUp(self):
        self.client = self.app.test_client()

    def test_unauthenticated_access_redirects(self):
        """Rotas protegidas de submissão e admin devem exigir autenticação."""
        res = self.client.get("/settings/contributions")
        self.assertEqual(res.status_code, 302)

        res2 = self.client.get("/machines/submit")
        self.assertEqual(res2.status_code, 302)

        res3 = self.client.get("/admin")
        self.assertEqual(res3.status_code, 302)

    def test_non_admin_forbidden_on_admin_routes(self):
        """Usuário comum autenticado recebe 403 Forbidden ao tentar acessar /admin."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "author_user"
            sess["role"] = "user"

        res = self.client.get("/admin")
        self.assertEqual(res.status_code, 403)

    def test_user_can_submit_machine_and_view_pipeline(self):
        """Usuário comum envia nova máquina com pacote ZIP e visualiza na lista e no detalhe."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "author_user"
            sess["role"] = "user"

        zip_buf = create_sample_zip()

        data = {
            "name": "Vuln Galaxy",
            "slug": "vuln-galaxy",
            "category": "Web",
            "author_difficulty": "Medium",
            "os_type": "Linux",
            "short_desc": "Laboratório demonstrativo de injeção",
            "root_flag": "DUNO{root_galaxy_777}",
            "package": (zip_buf, "vuln-galaxy.zip")
        }

        res = self.client.post("/api/machines/submit", data=data, content_type="multipart/form-data")
        self.assertIn(res.status_code, (200, 201))
        res_json = res.get_json()
        self.assertTrue(res_json.get("success"))
        sub_id = res_json["submission_id"]

        # Página de contribuições do usuário
        res_contrib = self.client.get("/settings/contributions")
        self.assertEqual(res_contrib.status_code, 200)
        self.assertIn("Vuln Galaxy", res_contrib.get_data(as_text=True))

        # Detalhes da submissão
        res_detail = self.client.get(f"/machines/submissions/{sub_id}")
        self.assertEqual(res_detail.status_code, 200)
        self.assertIn("SUBMITTED", res_detail.get_data(as_text=True))
        self.assertIn("vuln-galaxy", res_detail.get_data(as_text=True))

        # Adicionar comentário na thread
        res_comment = self.client.post(
            f"/api/machines/submissions/{sub_id}/comment",
            json={"comment": "Dúvida sobre a flag root"}
        )
        self.assertIn(res_comment.status_code, (200, 201))

    def test_admin_full_review_flow_and_publication(self):
        """Administrador analisa a máquina, roda build/scan/test e aprova para publicação."""
        # Cria uma máquina via API
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "author_user"
            sess["role"] = "user"

        zip_buf = create_sample_zip()
        data = {
            "name": "Target Zero",
            "slug": "target-zero",
            "category": "PrivEsc",
            "author_difficulty": "Easy",
            "os_type": "Linux",
            "short_desc": "Desafio de escalada de privilégios em container",
            "root_flag": "DUNO{target_zero_root}",
            "package": (zip_buf, "target-zero.zip")
        }
        res_sub = self.client.post("/api/machines/submit", data=data, content_type="multipart/form-data")
        sub_id = res_sub.get_json()["submission_id"]

        # Troca sessão para Admin
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "admin_master"
            sess["role"] = "admin"

        # 1. Dashboard Admin
        res_dash = self.client.get("/admin")
        self.assertEqual(res_dash.status_code, 200)
        self.assertIn("Painel de Revisão", res_dash.get_data(as_text=True))

        # 2. Fila de máquinas
        res_list = self.client.get("/admin/machines")
        self.assertEqual(res_list.status_code, 200)
        self.assertIn("Target Zero", res_list.get_data(as_text=True))

        # 3. Bancada de análise com 10 abas
        res_workspace = self.client.get(f"/admin/machines/{sub_id}")
        self.assertEqual(res_workspace.status_code, 200)
        html = res_workspace.get_data(as_text=True)
        self.assertIn("1. Visão Geral", html)
        self.assertIn("2. Arquivos", html)
        self.assertIn("3. Build", html)
        self.assertIn("4. Segurança", html)
        self.assertIn("9. Decisão &amp; Scorecard", html)

        # 4. API de leitura de arquivo
        res_file = self.client.get(f"/api/admin/machines/{sub_id}/file?path=manifest.yml")
        self.assertEqual(res_file.status_code, 200)
        self.assertIn("version:", res_file.get_json()["content"])

        # 5. Build
        res_build = self.client.post(f"/api/admin/machines/{sub_id}/build")
        self.assertEqual(res_build.status_code, 200)

        # 6. Scan
        res_scan = self.client.post(f"/api/admin/machines/{sub_id}/scan")
        self.assertEqual(res_scan.status_code, 200)

        # 7. Test
        res_test = self.client.post(f"/api/admin/machines/{sub_id}/test")
        self.assertEqual(res_test.status_code, 200)

        # 8. Calibrar Dificuldade
        res_diff = self.client.post(f"/api/admin/machines/{sub_id}/difficulty", json={"difficulty": "Medium"})
        self.assertEqual(res_diff.status_code, 200)

        # 9. Aprovar e Publicar
        res_pub = self.client.post(f"/api/admin/machines/{sub_id}/approve-publish", json={"reason": "Qualidade excelente"})
        self.assertEqual(res_pub.status_code, 200)

        # 10. Verificar catálogo de publicadas
        res_published_page = self.client.get("/admin/machines/published")
        self.assertEqual(res_published_page.status_code, 200)
        self.assertIn("Target Zero", res_published_page.get_data(as_text=True))

        # 11. Despublicar máquina
        res_unpub = self.client.post(f"/api/admin/machines/{sub_id}/unpublish", json={"reason": "Ajuste de laboratório"})
        self.assertEqual(res_unpub.status_code, 200)

        # 12. Auditoria
        res_audit = self.client.get("/admin/audit")
        self.assertEqual(res_audit.status_code, 200)
        self.assertIn("APPROVE_AND_PUBLISH", res_audit.get_data(as_text=True))
        self.assertIn("UNPUBLISH_MACHINE", res_audit.get_data(as_text=True))

    def test_command_center_renders_integrated_tabs_and_alias(self):
        """Verifica se o Command Center unificado (/settings e /command-center) renderiza todas as abas e telemetria."""
        # Não autenticado -> redirect
        res_anon = self.client.get("/settings")
        self.assertEqual(res_anon.status_code, 302)

        res_alias = self.client.get("/command-center")
        self.assertEqual(res_alias.status_code, 302)

        # Autenticado como Admin
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "admin_master"
            sess["role"] = "admin"

        res = self.client.get("/settings")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("COMMAND CENTER", html)
        self.assertIn("DUNO // COMMAND CENTER", html)
        self.assertIn("tab-btn-overview", html)
        self.assertIn("tab-btn-machines", html)
        self.assertIn("tab-btn-moderation", html)
        self.assertIn("tab-btn-system", html)
        self.assertIn("tab-btn-database", html)
        self.assertIn("pane-overview", html)
        self.assertIn("pane-machines", html)
        self.assertIn("pane-moderation", html)

    def test_published_machine_appears_in_catalog_with_notification_and_new_badge(self):
        """Valida se ao publicar máquina ela entra no catálogo, acende notificação e mostra selo NOVA MÁQUINA."""
        # 1. Login como usuário normal e submete máquina
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "aluno_tester"
            sess["role"] = "user"

        zip_buf = create_sample_zip()
        data = {
            "name": "Datacenter Test Box",
            "slug": "datacenter-test-box",
            "author_difficulty": "Medium",
            "category": "Web",
            "os_type": "Linux",
            "short_desc": "Desafio de teste de publicação",
            "full_desc": "Descrição detalhada do laboratório",
            "user_flag": "FLAG{user_flag_123}",
            "root_flag": "FLAG{root_flag_999}",
            "package": (zip_buf, "datacenter_test.zip")
        }
        res_sub = self.client.post("/api/machines/submit", data=data, content_type="multipart/form-data")
        self.assertEqual(res_sub.status_code, 200)
        sub_id = res_sub.get_json()["submission_id"]

        # 2. Login como Admin e publica
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["username"] = "admin_master"
            sess["role"] = "admin"

        res_pub = self.client.post(f"/api/admin/machines/{sub_id}/approve-publish", json={"reason": "Aprovada"})
        self.assertEqual(res_pub.status_code, 200)
        self.assertEqual(res_pub.get_json()["status"], "PUBLISHED")
        ch_id = res_pub.get_json()["challenge_id"]

        # 3. Verifica se a pasta do desafio foi criada para o Runner
        ch_path = Path("challenges") / ch_id
        self.assertTrue(ch_path.exists(), "Pasta challenges/machine-<slug> deve ser criada na publicação")

        # 4. Login como usuário normal e consulta notificações
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "aluno_tester"
            sess["role"] = "user"

        res_notif = self.client.get("/api/notifications")
        self.assertEqual(res_notif.status_code, 200)
        notif_data = res_notif.get_json()
        self.assertGreaterEqual(notif_data["unread_count"], 1)
        self.assertTrue(any(n["target_id"] == ch_id for n in notif_data["notifications"]))

        # 5. Acessa catálogo /challenges e confere se card aparece com NOVA MÁQUINA
        res_cat = self.client.get("/challenges")
        self.assertEqual(res_cat.status_code, 200)
        cat_html = res_cat.get_data(as_text=True)
        self.assertIn("Datacenter Test Box", cat_html)
        self.assertIn("NOVA MÁQUINA", cat_html)

        # 6. Acessa o desafio para marcar como visualizado
        res_detail = self.client.get(f"/challenges/{ch_id}")
        self.assertEqual(res_detail.status_code, 200)

        # 7. Recarrega /challenges e o badge NOVA MÁQUINA não deve mais aparecer para este desafio
        res_cat_again = self.client.get("/challenges")
        cat_html_again = res_cat_again.get_data(as_text=True)
        self.assertNotIn(f'id="badge-new-{ch_id}"', cat_html_again)

        # 8. Marca notificações como lidas
        res_mark = self.client.post("/api/notifications/mark-read")
        self.assertEqual(res_mark.status_code, 200)
        res_notif_after = self.client.get("/api/notifications")
        self.assertEqual(res_notif_after.get_json()["unread_count"], 0)

        # 9. Valida resolução de flag via solves_service
        from modules.challenges.solves_service import solves_service
        with self.app.app_context():
            ok, status, pts, msg = solves_service.submit_flag(1, ch_id, "FLAG{user_flag_123}")
            self.assertTrue(ok, f"Flag deve ser validada: {msg}")
            self.assertEqual(status, "solved")

        # Limpeza do diretório de teste
        import shutil
        if ch_path.exists():
            shutil.rmtree(ch_path, ignore_errors=True)


