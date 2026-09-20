"""tests/test_challenge_routes.py — Testes de rotas HTTP do catálogo de desafios CTF."""
import os
import tempfile
import sqlite3
import unittest
from pathlib import Path
from werkzeug.security import generate_password_hash


class TestChallengeRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Cria banco SQLite temporário isolado para os testes de rota
        cls.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.tmp_db.name
        cls.tmp_db.close()
        os.environ["DATABASE"] = cls.db_path

        # Inicializa schema mínimo do DUNO
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
        INSERT INTO users (id, username, password_hash, role)
        VALUES (1, 'testuser', 'hash', 'user');
        """)
        conn.commit()
        conn.close()

        from app import create_app
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["DATABASE"] = cls.db_path

    def setUp(self):
        self.client = self.app.test_client()

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.db_path)
        except OSError:
            pass

    def test_get_challenges_without_auth_redirects_to_login(self):
        """Acesso desautenticado a /challenges deve redirecionar para /login (302)."""
        response = self.client.get("/challenges")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_get_challenges_with_auth_returns_200(self):
        """Usuário autenticado deve receber 200 OK em /challenges."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/challenges")
        self.assertEqual(response.status_code, 200)

    def test_challenges_render_in_pure_ssr_on_first_paint(self):
        """Os cards de desafios devem estar presentes no HTML retornado pelo servidor."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/challenges")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        # Verifica a presença de desafios chave do catálogo de 25 itens
        expected_challenges = [
            "alpha-sqli-basics",
            "bravo",
            "hotel-junior-dev-challenge",
            "zulu-koa-devtools",
        ]
        for cid in expected_challenges:
            self.assertIn(cid, html, f"Desafio '{cid}' não foi encontrado no HTML SSR inicial.")

        # Verifica elementos obrigatórios do card redesenhado
        self.assertIn("POINTS", html)
        self.assertIn("XP", html)
        self.assertIn("MACHINE", html)
        self.assertIn("DIFFICULTY", html)
        self.assertIn("DESCRIPTION", html)
        self.assertIn("Start Machine", html)
        self.assertIn("Linux", html)

        # Links diretos para páginas individuais
        self.assertIn('/desafio/1', html)
        self.assertIn('/desafio/2', html)
        self.assertIn('/desafio/25', html)

        # Controles de paginação presentes
        self.assertIn('id="pagination-container"', html)
        self.assertIn('id="pagination-prev"', html)
        self.assertIn('id="pagination-next"', html)

        # Card limpo NÃO deve conter botões de ação ou submissão direta
        self.assertNotIn("ENVIAR FLAG", html)

        # Tags foram removidas para não dar spoiler e reduzir altura
        self.assertNotIn("hcard-tags-row", html)
        self.assertIn("challenge-card-running-bar", html)
        self.assertIn("js-copy-target-ip", html)

    def test_get_desafio_by_numeric_index_authenticated(self):
        """Acesso autenticado a /desafio/1 retorna a página completa do desafio Alpha."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/desafio/1")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        self.assertIn("Alpha", html)
        self.assertIn("Start Machine", html)
        self.assertIn("VALIDAR", html)
        self.assertIn("DESCRIPTION", html)

    def test_get_desafio_by_numeric_index_2(self):
        """Acesso autenticado a /desafio/2 carrega o segundo desafio do catálogo (Bravo)."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/desafio/2")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Bravo", html)

    def test_get_desafio_by_slug(self):
        """Acesso autenticado a /desafio/<slug> também é suportado com código 200."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/desafio/delta-idor-document-vault")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Foxtrot", html)

    def test_get_desafio_unauthenticated_redirects_to_login(self):
        """Acesso não autenticado a /desafio/<id> deve redirecionar para /login."""
        response = self.client.get("/desafio/1")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

    def test_get_desafio_invalid_index_or_id_returns_404(self):
        """Índice fora do limite, slug inexistente ou path traversal retorna 404."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        res_bounds_high = self.client.get("/desafio/26")
        self.assertEqual(res_bounds_high.status_code, 404)

        res_bounds = self.client.get("/desafio/999")
        self.assertEqual(res_bounds.status_code, 404)

        res_none = self.client.get("/desafio/non-existent-challenge-id")
        self.assertEqual(res_none.status_code, 404)

        res_trav = self.client.get("/desafio/..%2f..%2fetc%2fpasswd")
        self.assertEqual(res_trav.status_code, 404)

    def test_get_desafio_25_zenith(self):
        """Acesso autenticado a /desafio/25 carrega a última máquina (Zenith)."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"

        response = self.client.get("/desafio/25")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Zenith", html)

    # ── Testes de API REST do Runner (Fase 3) ──────────────────────────────────

    def test_api_start_instance_requires_csrf(self):
        """POST /api/challenges/<id>/instances sem CSRF deve retornar 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = "valid-secret-csrf"

        res = self.client.post("/api/challenges/hotel-junior-dev-challenge/instances")
        self.assertEqual(res.status_code, 403)

    def test_api_start_instance_success_and_rate_limit(self):
        """START com CSRF retorna 201; segundo START imediato deve retornar 429 com Retry-After."""
        from modules.challenges.rate_limiter import rate_limiter
        rate_limiter.reset_for_testing()

        csrf = "test-csrf-token-12345"
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = csrf

        # 1. Primeiro START: sucesso (201)
        res1 = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/instances",
            headers={"X-CSRFToken": csrf},
        )
        self.assertEqual(res1.status_code, 201)
        data1 = res1.get_json()
        self.assertIn("instance_id", data1)
        instance_id = data1["instance_id"]

        # 2. Segundo START imediato para outro desafio: bloqueado por rate limit (429)
        res2 = self.client.post(
            "/api/challenges/golf-static-analysis-config/instances",
            headers={"X-CSRFToken": csrf},
        )
        self.assertEqual(res2.status_code, 429)
        self.assertIn("Retry-After", res2.headers)
        self.assertGreater(int(res2.headers["Retry-After"]), 0)

        # 3. GET status da instância criada retorna 200
        res_st = self.client.get(f"/api/challenge-instances/{instance_id}")
        self.assertEqual(res_st.status_code, 200)
        data_st = res_st.get_json()
        self.assertEqual(data_st["instance_id"], instance_id)

        # 4. RENEW da instância (+1 hora)
        res_renew = self.client.post(
            f"/api/challenge-instances/{instance_id}/renew",
            headers={"X-CSRFToken": csrf},
        )
        self.assertEqual(res_renew.status_code, 200)
        self.assertEqual(res_renew.get_json()["status"], "success")

        # 5. STOP da instância retorna 200
        res_stop = self.client.post(
            f"/api/challenge-instances/{instance_id}/stop",
            headers={"X-CSRFToken": csrf},
        )
        self.assertEqual(res_stop.status_code, 200)
        self.assertEqual(res_stop.get_json()["status"], "stopped")

    def test_walkthrough_renders_running_instance_and_timer(self):
        """Página /desafio/1/walkthrough com instância ativa renderiza o IP do alvo e card de contagem regressiva."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "testuser"
            sess["role"] = "user"
            sess["csrf_token"] = "csrf-test-token"

        # Insere instância mock ativa no banco de teste
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO challenge_instances (id, challenge_id, user_id, container_ref, status, endpoint, expires_at)
               VALUES ('mock-inst-1', 'alpha-sqli-basics', 1, 'ref-1', 'running', 'http://10.10.15.11:5000', '2026-09-17 04:00:00')"""
        )
        conn.commit()
        conn.close()

        res = self.client.get("/desafio/1/walkthrough")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn("10.10.15.11:5000", html)
        self.assertIn("wt-target-bar", html)
        self.assertIn("wt-session-card", html)
        self.assertIn("btn-renew-time", html)
        self.assertIn("js-copy-wt-ip", html)

    def test_bravo_walkthrough_and_hybrid_flags(self):
        """Walkthrough do desafio 2 (Bravo) renderiza 200, com flags híbridas DUNO{hash}."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = "mock-csrf"

        res = self.client.get("/desafio/2/walkthrough")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        self.assertIn("Bravo", html)
        self.assertIn("Weak JWT & SSTI", html)
        self.assertIn("DUNO{5d41402abc4b2a76b9719d911017c592}", html)
        self.assertIn("DUNO{7c6a180b36896a0a8c02787eeafb0e4c}", html)
        self.assertIn("DUNO{9e107d9d372bb6826bd81d3542a419d6}", html)
        self.assertIn("solve_bravo.py", html)
        self.assertIn("wt-target-bar", html)
        self.assertIn("nf-md-target", html)

        # Teste de validação de flag híbrida via API
        flag_res = self.client.post(
            "/api/challenges/bravo/submit",
            json={"flag": "DUNO{9e107d9d372bb6826bd81d3542a419d6}"},
            headers={"X-CSRFToken": "mock-csrf"},
        )
        self.assertEqual(flag_res.status_code, 200)
        data = flag_res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["points_awarded"], 1150)


if __name__ == "__main__":
    unittest.main()


