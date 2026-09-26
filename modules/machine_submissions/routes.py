"""modules/machine_submissions/routes.py — Rotas de usuário para Submissão e Gerenciamento de Máquinas."""
import os
import json
import re
import shutil
import hashlib
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, current_app
from werkzeug.utils import secure_filename
from core.decorators import login_required
from core.auth import current_user
from core.database import get_db
from modules.machine_submissions.db import init_submissions_db, log_machine_audit, create_platform_notification
from modules.machine_submissions.state_machine import transition_submission, StateTransitionError
from modules.machine_submissions.validator import extract_package, validate_extracted_structure, ValidationError
from modules.machine_submissions.worker import run_scan_job

bp = Blueprint("submissions", __name__)

UPLOAD_DIR = Path("static/uploads/machine_submissions")
SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_PACKAGE_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_WALKTHROUGH_CHARS = 200_000  # limite do walkthrough em Markdown (~200 KB)


def _read_package_walkthrough(extract_dir) -> str:
    """Lê walkthrough.md da raiz do pacote extraído (convenção p/ botão View Walkthrough)."""
    try:
        base = Path(extract_dir)
        for cand in (base / "walkthrough.md", base / "WALKTHROUGH.md"):
            if cand.is_file() and cand.stat().st_size <= MAX_WALKTHROUGH_CHARS:
                return cand.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        pass
    return ""



@bp.before_request
def ensure_db():
    db = get_db()
    init_submissions_db(db)


# ══════════════════════════════════════════════════════════════════════════════
# 1. PÁGINAS DO USUÁRIO
# ══════════════════════════════════════════════════════════════════════════════

@bp.route("/settings/contributions")
@bp.route("/contributions")
@login_required
def contributions():
    """Página 'Minhas contribuições' exibindo a lista de submissões do usuário."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db()

    rows = db.execute(
        """SELECT s.id, s.slug, s.name, s.status, s.current_version, s.created_at, s.updated_at, s.published_at,
                  m.os_type, m.author_difficulty, m.category, m.short_desc,
                  (SELECT r.reason FROM machine_reviews r WHERE r.submission_id = s.id ORDER BY r.id DESC LIMIT 1) as last_review_reason,
                  (SELECT r.decision FROM machine_reviews r WHERE r.submission_id = s.id ORDER BY r.id DESC LIMIT 1) as last_decision
           FROM machine_submissions s
           LEFT JOIN machine_metadata m ON m.submission_id = s.id AND m.version_id = (
               SELECT id FROM machine_versions v WHERE v.submission_id = s.id ORDER BY v.id DESC LIMIT 1
           )
           WHERE s.user_id = ?
           ORDER BY s.updated_at DESC""",
        (user["id"],)
    ).fetchall()

    return render_template("submissions/contributions.html", submissions=rows, user=user)


@bp.route("/machines/submit", methods=["GET"])
@login_required
def submit_page():
    """Página dedicada para criação e envio de nova máquina com formulário estruturado."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return render_template("submissions/submit.html", user=user)


@bp.route("/machines/submissions/<int:submission_id>", methods=["GET"])
@login_required
def submission_detail(submission_id):
    """Página de acompanhamento da submissão para o autor."""
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    db = get_db()

    sub = db.execute(
        """SELECT s.*, u.username as author_name
           FROM machine_submissions s
           JOIN users u ON u.id = s.user_id
           WHERE s.id = ?""",
        (submission_id,)
    ).fetchone()

    if not sub:
        abort(404)

    # Apenas o autor ou admin pode ver
    if sub["user_id"] != user["id"] and user.get("role") != "admin":
        abort(403)

    # Marca notificações como lidas para o usuário visualizador
    try:
        notifs = db.execute(
            "SELECT id FROM platform_notifications WHERE target_id = ? OR link LIKE ?",
            (str(submission_id), f"%/submissions/{submission_id}%")
        ).fetchall()
        for n in notifs:
            db.execute(
                "INSERT OR IGNORE INTO user_notification_reads (user_id, notification_id) VALUES (?, ?)",
                (user["id"], n["id"])
            )
        db.commit()
    except Exception:
        pass

    # Versões
    versions = db.execute(
        "SELECT * FROM machine_versions WHERE submission_id = ? ORDER BY id DESC",
        (submission_id,)
    ).fetchall()

    latest_ver = versions[0] if versions else None
    metadata = None
    files = []
    if latest_ver:
        metadata = db.execute("SELECT * FROM machine_metadata WHERE version_id = ?", (latest_ver["id"],)).fetchone()
        files = db.execute("SELECT * FROM machine_files WHERE version_id = ?", (latest_ver["id"],)).fetchall()

    # Comentários
    comments = db.execute(
        """SELECT c.*, u.username
           FROM machine_review_comments c
           JOIN users u ON u.id = c.user_id
           WHERE c.submission_id = ?
           ORDER BY c.created_at ASC""",
        (submission_id,)
    ).fetchall()

    # Histórico de estados
    history = db.execute(
        """SELECT h.*, u.username as changed_by
           FROM machine_status_history h
           LEFT JOIN users u ON u.id = h.changed_by_user_id
           WHERE h.submission_id = ?
           ORDER BY h.created_at DESC""",
        (submission_id,)
    ).fetchall()

    return render_template(
        "submissions/submission_detail.html",
        sub=sub,
        latest_ver=latest_ver,
        metadata=metadata,
        files=files,
        comments=comments,
        history=history,
        user=user
    )


# ══════════════════════════════════════════════════════════════════════════════
# 2. ENDPOINTS DE API (SUBMISSÃO E INTERAÇÃO)
# ══════════════════════════════════════════════════════════════════════════════

@bp.route("/api/machines/submit", methods=["POST"])
@login_required
def api_submit_machine():
    """Recebe metadados e o arquivo compactado da máquina, valida e cria submissão."""
    user = current_user()
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    db = get_db()

    # Dados do formulário
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower()
    short_desc = request.form.get("short_desc", "").strip()
    full_desc = request.form.get("full_desc", "").strip()
    os_type = request.form.get("os_type", "Linux").strip()
    os_distro = request.form.get("os_distro", "").strip()
    architecture = request.form.get("architecture", "amd64").strip()
    difficulty = (request.form.get("author_difficulty") or request.form.get("difficulty") or "Medium").strip()
    category = request.form.get("category", "Web").strip()
    version_str = request.form.get("version", "1.0").strip()

    # Informações educacionais
    objectives_raw = request.form.get("objectives", "").strip()
    prerequisites_raw = request.form.get("prerequisites", "").strip()
    skills_developed = request.form.get("skills_developed", "").strip()
    scenario_intro = request.form.get("scenario_intro", "").strip()
    hints_raw = request.form.get("hints", "").strip()
    references_raw = request.form.get("references", "").strip()
    user_flag = request.form.get("user_flag", "").strip()
    root_flag = request.form.get("root_flag", "").strip()
    walkthrough_md = request.form.get("walkthrough_md", "").strip()

    if not name or not short_desc:
        return jsonify({"status": "error", "error": "Nome e descrição curta são obrigatórios."}), 400

    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not SLUG_REGEX.match(slug):
        return jsonify({"status": "error", "error": "Slug inválido. Use apenas letras minúsculas, números e hífens."}), 400

    # Verifica duplicidade de slug
    existing = db.execute("SELECT id FROM machine_submissions WHERE slug = ?", (slug,)).fetchone()
    if existing:
        return jsonify({
            "status": "error",
            "error": f"Já existe uma máquina cadastrada com o slug '{slug}'. Escolha um novo slug ou acesse a submissão existente.",
            "existing_submission_id": existing["id"],
            "redirect_url": url_for("submissions.submission_detail", submission_id=existing["id"])
        }), 400

    # Upload do arquivo
    file = request.files.get("package")
    if not file or not file.filename:
        return jsonify({"error": "Arquivo de pacote (.zip ou .tar.gz) é obrigatório."}), 400

    if request.content_length and request.content_length > MAX_PACKAGE_UPLOAD_BYTES:
        return jsonify({"error": f"O arquivo enviado excede o limite máximo permitido de {MAX_PACKAGE_UPLOAD_BYTES // (1024*1024)}MB."}), 413

    filename = secure_filename(file.filename)
    if not filename.lower().endswith((".zip", ".tar.gz", ".tar")):
        return jsonify({"error": "Formato de arquivo inválido. Apenas .zip e .tar.gz são permitidos."}), 400

    # Salva arquivo temporário
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pkg_path = UPLOAD_DIR / f"{slug}_v{version_str}_{filename}"
    file.save(pkg_path)

    # Verifica tamanho real em disco
    if pkg_path.stat().st_size > MAX_PACKAGE_UPLOAD_BYTES:
        pkg_path.unlink(missing_ok=True)
        return jsonify({"error": f"O arquivo enviado excede o limite máximo de {MAX_PACKAGE_UPLOAD_BYTES // (1024*1024)}MB."}), 413

    # Extração segura com ZipSlip, ZipBomb e Symlink protection
    extract_dir = UPLOAD_DIR / f"extracted_{slug}_v{version_str}"
    try:
        extracted_files = extract_package(str(pkg_path), str(extract_dir))
        manifest = validate_extracted_structure(str(extract_dir))
    except ValidationError as ve:
        # Limpa em caso de erro
        pkg_path.unlink(missing_ok=True)
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        return jsonify({"error": f"Erro de validação no pacote: {ve}"}), 400
    except Exception as e:
        pkg_path.unlink(missing_ok=True)
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        return jsonify({"error": f"Falha ao descompactar arquivo: {e}"}), 400

    # Serializa campos educacionais em JSON
    objectives_list = [o.strip() for o in objectives_raw.splitlines() if o.strip()]
    prereq_list = [p.strip() for p in prerequisites_raw.splitlines() if p.strip()]
    hints_list = [h.strip() for h in hints_raw.splitlines() if h.strip()]
    ref_list = [r.strip() for r in references_raw.splitlines() if r.strip()]

    # Walkthrough: campo do formulário tem prioridade; senão, importa walkthrough.md do pacote
    if not walkthrough_md:
        walkthrough_md = _read_package_walkthrough(extract_dir)

    # Cria submissão no banco
    cur = db.execute(
        """INSERT INTO machine_submissions (slug, name, user_id, status, current_version)
           VALUES (?, ?, ?, 'SUBMITTED', ?)""",
        (slug, name, user["id"], version_str)
    )
    sub_id = cur.lastrowid

    # Cria versão
    cur = db.execute(
        """INSERT INTO machine_versions (submission_id, version_str, package_path, extracted_path, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (sub_id, version_str, str(pkg_path), str(extract_dir), "Submissão inicial do autor.")
    )
    ver_id = cur.lastrowid

    # Salva metadados
    db.execute(
        """INSERT INTO machine_metadata (
               submission_id, version_id, short_desc, full_desc, os_type, os_distro,
               architecture, author_difficulty, category, objectives_json, prerequisites_json,
               skills_developed, scenario_intro, hints_json, references_json, walkthrough_md, exposed_ports_json,
               cpu_limit, memory_limit_mb, disk_limit_mb
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            sub_id, ver_id, short_desc, full_desc, os_type, os_distro,
            architecture, difficulty, category, json.dumps(objectives_list), json.dumps(prereq_list),
            skills_developed, scenario_intro, json.dumps(hints_list), json.dumps(ref_list), walkthrough_md or None,
            json.dumps(manifest.get("runtime", {}).get("exposed_ports", [80])),
            float(manifest.get("resources", {}).get("cpu", 1.0)),
            int(manifest.get("resources", {}).get("memory", 1024)),
            int(manifest.get("resources", {}).get("disk", 5120))
        )
    )

    # Indexa arquivos
    for f in extracted_files:
        db.execute(
            """INSERT INTO machine_files (version_id, file_path, file_size, is_critical, sha256)
               VALUES (?, ?, ?, ?, ?)""",
            (ver_id, f["file_path"], f["file_size"], f["is_critical"], f["sha256"])
        )

    # Salva flags de forma segura (hash SHA256)
    import hashlib
    if user_flag:
        u_hash = hashlib.sha256(user_flag.encode()).hexdigest()
        db.execute(
            """INSERT INTO machine_flags (submission_id, version_id, flag_type, flag_hash, is_present, location_hint)
               VALUES (?, ?, 'user', ?, 1, 'Flag de usuário inicial')""",
            (sub_id, ver_id, u_hash)
        )
    if root_flag:
        r_hash = hashlib.sha256(root_flag.encode()).hexdigest()
        db.execute(
            """INSERT INTO machine_flags (submission_id, version_id, flag_type, flag_hash, is_present, location_hint)
               VALUES (?, ?, 'root', ?, 1, 'Flag de root final')""",
            (sub_id, ver_id, r_hash)
        )

    # Histórico de transição
    db.execute(
        """INSERT INTO machine_status_history (submission_id, from_status, to_status, changed_by_user_id, reason)
           VALUES (?, 'DRAFT', 'SUBMITTED', ?, 'Envio inicial da máquina para análise')""",
        (sub_id, user["id"])
    )

    # Log de auditoria
    log_machine_audit(
        db, user["id"], "SUBMIT_MACHINE", "machine_submissions", str(sub_id),
        "SUCCESS", request.remote_addr, {"slug": slug, "version": version_str}
    )

    # Dispara scan estático preliminar automaticamente
    run_scan_job(db, ver_id)

    # Notificação na plataforma para administradores
    create_platform_notification(
        db,
        ntype="machine_submitted",
        title=f"Nova Máquina Submetida: {name}",
        message=f"A máquina '{name}' ({slug} v{version_str}) foi enviada por @{user['username']} e aguarda moderação.",
        link=url_for("submissions_admin.machine_review_workspace", submission_id=sub_id),
        target_id=str(sub_id),
        target_role="admin"
    )

    db.commit()
    return jsonify({
        "status": "success",
        "success": True,
        "submission_id": sub_id,
        "slug": slug,
        "redirect_url": url_for("submissions.submission_detail", submission_id=sub_id)
    })


@bp.route("/api/machines/submissions/<int:submission_id>/comment", methods=["POST"])
@login_required
def api_add_comment(submission_id):
    """Adiciona comentário ou resposta na submissão."""
    user = current_user()
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    db = get_db()

    sub = db.execute("SELECT id, user_id FROM machine_submissions WHERE id = ?", (submission_id,)).fetchone()
    if not sub:
        return jsonify({"error": "Submissão não encontrada"}), 404

    if sub["user_id"] != user["id"] and user.get("role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403

    data = request.get_json(silent=True) or {}
    text = str(data.get("comment", "")).strip()
    if not text:
        return jsonify({"error": "Comentário não pode estar vazio"}), 400

    role = "admin" if user.get("role") == "admin" else "author"
    db.execute(
        """INSERT INTO machine_review_comments (submission_id, user_id, author_role, comment_text)
           VALUES (?, ?, ?, ?)""",
        (submission_id, user["id"], role, text)
    )
    db.commit()

    return jsonify({"success": True, "author": user["username"], "role": role, "comment": text})


@bp.route("/api/machines/submissions/<int:submission_id>/resubmit", methods=["POST"])
@login_required
def api_resubmit_version(submission_id):
    """Permite ao autor enviar nova versão da máquina após CHANGES_REQUESTED."""
    user = current_user()
    if not user:
        return jsonify({"error": "Não autenticado"}), 401
    db = get_db()

    sub = db.execute("SELECT * FROM machine_submissions WHERE id = ?", (submission_id,)).fetchone()
    if not sub:
        return jsonify({"error": "Submissão não encontrada"}), 404

    if sub["user_id"] != user["id"]:
        return jsonify({"error": "Apenas o autor pode enviar nova versão"}), 403

    if sub["status"] not in ("CHANGES_REQUESTED", "DRAFT"):
        return jsonify({"error": f"Não é possível reenviar uma máquina com status '{sub['status']}'"}), 400

    version_str = request.form.get("version", "").strip()
    notes = request.form.get("notes", "Correções enviadas pelo autor").strip()

    file = request.files.get("package")
    if not file or not file.filename:
        return jsonify({"error": "Arquivo de pacote é obrigatório."}), 400

    if not version_str:
        # Incrementa versão menor automaticamente
        curr = sub["current_version"] or "1.0"
        try:
            parts = curr.split(".")
            version_str = f"{parts[0]}.{int(parts[1]) + 1}"
        except Exception:
            version_str = "1.1"

    if request.content_length and request.content_length > MAX_PACKAGE_UPLOAD_BYTES:
        return jsonify({"error": f"O arquivo enviado excede o limite máximo de {MAX_PACKAGE_UPLOAD_BYTES // (1024*1024)}MB."}), 413

    filename = secure_filename(file.filename)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    pkg_path = UPLOAD_DIR / f"{sub['slug']}_v{version_str}_{filename}"
    file.save(pkg_path)

    if pkg_path.stat().st_size > MAX_PACKAGE_UPLOAD_BYTES:
        pkg_path.unlink(missing_ok=True)
        return jsonify({"error": f"O arquivo enviado excede o limite máximo de {MAX_PACKAGE_UPLOAD_BYTES // (1024*1024)}MB."}), 413

    extract_dir = UPLOAD_DIR / f"extracted_{sub['slug']}_v{version_str}"
    try:
        extracted_files = extract_package(str(pkg_path), str(extract_dir))
        manifest = validate_extracted_structure(str(extract_dir))
    except Exception as e:
        pkg_path.unlink(missing_ok=True)
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        return jsonify({"error": f"Erro na validação do novo pacote: {e}"}), 400

    # Cria nova versão
    cur = db.execute(
        """INSERT INTO machine_versions (submission_id, version_str, package_path, extracted_path, notes)
           VALUES (?, ?, ?, ?, ?)""",
        (submission_id, version_str, str(pkg_path), str(extract_dir), notes)
    )
    ver_id = cur.lastrowid

    # Copia metadados atualizados
    old_meta = db.execute(
        "SELECT * FROM machine_metadata WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if old_meta:
        # Walkthrough da nova versão: override do formulário > walkthrough.md do pacote > versão anterior
        new_walkthrough = (request.form.get("walkthrough_md", "").strip()
                           or _read_package_walkthrough(extract_dir)
                           or old_meta["walkthrough_md"])
        db.execute(
            """INSERT INTO machine_metadata (
                   submission_id, version_id, short_desc, full_desc, os_type, os_distro,
                   architecture, author_difficulty, category, objectives_json, prerequisites_json,
                   skills_developed, scenario_intro, hints_json, references_json, walkthrough_md, exposed_ports_json,
                   cpu_limit, memory_limit_mb, disk_limit_mb
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                submission_id, ver_id, old_meta["short_desc"], old_meta["full_desc"],
                old_meta["os_type"], old_meta["os_distro"], old_meta["architecture"],
                old_meta["author_difficulty"], old_meta["category"], old_meta["objectives_json"],
                old_meta["prerequisites_json"], old_meta["skills_developed"], old_meta["scenario_intro"],
                old_meta["hints_json"], old_meta["references_json"], new_walkthrough or None, old_meta["exposed_ports_json"],
                old_meta["cpu_limit"], old_meta["memory_limit_mb"], old_meta["disk_limit_mb"]
            )
        )

    # Indexa novos arquivos
    for f in extracted_files:
        db.execute(
            """INSERT INTO machine_files (version_id, file_path, file_size, is_critical, sha256)
               VALUES (?, ?, ?, ?, ?)""",
            (ver_id, f["file_path"], f["file_size"], f["is_critical"], f["sha256"])
        )

    # Atualiza versão corrente e transiciona estado para SUBMITTED
    db.execute(
        "UPDATE machine_submissions SET current_version = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (version_str, submission_id)
    )
    transition_submission(db, submission_id, "SUBMITTED", user["id"], f"Reenvio de versão {version_str} com correções")

    # Roda scan estático na nova versão
    run_scan_job(db, ver_id)

    # Notificação na plataforma para administradores
    create_platform_notification(
        db,
        ntype="machine_submitted",
        title=f"Nova Versão Submetida: {sub['name']} (v{version_str})",
        message=f"Uma nova versão da máquina '{sub['name']}' foi reenviada por @{user['username']} para revisão.",
        link=url_for("submissions_admin.machine_review_workspace", submission_id=submission_id),
        target_id=str(submission_id),
        target_role="admin"
    )

    db.commit()
    return jsonify({"success": True, "version": version_str, "status": "SUBMITTED"})
