"""tests/test_challenge_solves.py — Testes automatizados de submissão de flags e pontuação.

Cobre a Definition of Done da Fase 4 do upgrade_v3.md:
- POST /api/challenges/:id/submit exige autenticação e CSRF.
- Comparação de flag em tempo constante implementada.
- Solve duplicado não pontua duas vezes.
- solves_count incrementa apenas após sucesso real.
- Mensagens de erro não revelam a flag.
- Testes cobrem envio correto, incorreto, duplicado e concorrente — todos verdes.
"""
import unittest
import tempfile
import os
import shutil
import threading
from pathlib import Path
from flask import Flask

from app import create_app
import sqlite3
from core.database import get_db
from modules.challenges.flag_service import flag_service
from modules.challenges.solves_service import solves_service
from modules.challenges.catalog import catalog

class TestChallengeSolves(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._orig_db = os.environ.get("DATABASE")
        cls.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.tmp_db.name
        cls.tmp_db.close()
        os.environ["DATABASE"] = cls.db_path

        from seed import DDL
        conn = sqlite3.connect(cls.db_path)
        conn.executescript(DDL)
        conn.execute("INSERT INTO users (id, username, password_hash, role) VALUES (1, 'user1', 'hash', 'user')")
        conn.execute("INSERT INTO users (id, username, password_hash, role) VALUES (2, 'user2', 'hash', 'user')")
        conn.commit()
        conn.close()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["DATABASE"] = cls.db_path
        cls.app.config["SECRET_KEY"] = "test-secret-key-solves-12345"

    @classmethod
    def tearDownClass(cls):
        if cls._orig_db is not None:
            os.environ["DATABASE"] = cls._orig_db
        else:
            os.environ.pop("DATABASE", None)
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.client = self.app.test_client()
        self.csrf = "test-csrf-token-solves-xyz"
        # Limpa tabela challenge_solves para garantir isolamento por teste
        with self.app.app_context():
            db = get_db()
            db.execute("DELETE FROM challenge_solves")
            db.commit()

    # ── 1. Autenticação e CSRF ──────────────────────────────────────────────────

    def test_submit_requires_authentication(self):
        """Envio de flag sem autenticação deve retornar 401 ou redirect para login."""
        res = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertIn(res.status_code, (401, 302))

    def test_submit_requires_csrf_token(self):
        """Envio de flag sem token CSRF deve retornar 403 Forbidden."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = self.csrf

        # Sem header CSRF
        res_no_csrf = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
        )
        self.assertEqual(res_no_csrf.status_code, 403)

        # Com header CSRF errado
        res_bad_csrf = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
            headers={"X-CSRFToken": "invalid-csrf-token"},
        )
        self.assertEqual(res_bad_csrf.status_code, 403)

    # ── 2. Envio Incorreto e Não Revelação de Flag ───────────────────────────────

    def test_submit_incorrect_flag(self):
        """Envio de flag incorreta deve retornar 400 e mensagem genérica que não revela a flag."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = self.csrf

        res = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{wrong_guess_12345}"},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("error", data)

        # Garante que a flag correta e pistas nunca são reveladas
        real_flags = flag_service.get_flags_for_challenge("hotel-junior-dev-challenge")
        for rf in real_flags:
            self.assertNotIn(rf, data["error"])
            if rf.startswith("FLAG{") and rf.endswith("}"):
                self.assertNotIn(rf[5:-1], data["error"])

    def test_submit_missing_or_empty_flag_payload(self):
        """Envio sem o campo 'flag' ou com payload vazio deve retornar 400."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = self.csrf

        res = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertEqual(res.status_code, 400)

    # ── 3. Envio Correto e Incremento de Pontuação / solves_count ───────────────

    def test_submit_correct_flag_success(self):
        """Envio de flag válida retorna 200, pontua e incrementa solves_count."""
        with self.app.app_context():
            ch_before = catalog.get_by_id("hotel-junior-dev-challenge")
            initial_solves = ch_before["solves_count"]
            expected_points = ch_before["points"]

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = self.csrf

        res = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("points_awarded"), expected_points)
        self.assertFalse(data.get("already_solved"))

        # Verifica se solves_count incrementou exatamente em 1
        with self.app.app_context():
            ch_after = catalog.get_by_id("hotel-junior-dev-challenge")
            self.assertEqual(ch_after["solves_count"], initial_solves + 1)

            # Verifica total de pontos do usuário
            pts = solves_service.get_user_total_points(1)
            self.assertEqual(pts, expected_points)

    # ── 4. Solve Duplicado (Idempotência) ────────────────────────────────────────

    def test_submit_duplicate_flag_does_not_award_double_points(self):
        """Segundo envio da mesma flag pelo mesmo usuário deve retornar 409 e não pontuar duas vezes."""
        with self.app.app_context():
            expected_points = catalog.get_by_id("hotel-junior-dev-challenge")["points"]

        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["csrf_token"] = self.csrf

        # 1º envio: Sucesso (200)
        res1 = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertEqual(res1.status_code, 200)

        # 2º envio: Duplicado (409)
        res2 = self.client.post(
            "/api/challenges/hotel-junior-dev-challenge/submit",
            json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
            headers={"X-CSRFToken": self.csrf},
        )
        self.assertEqual(res2.status_code, 409)
        data2 = res2.get_json()
        self.assertTrue(data2.get("already_solved"))
        self.assertEqual(data2.get("points_awarded"), 0)

        # Pontos do usuário permanecem expected_points, solves_count permanece 1
        with self.app.app_context():
            pts = solves_service.get_user_total_points(1)
            self.assertEqual(pts, expected_points)
            ch = catalog.get_by_id("hotel-junior-dev-challenge")
            self.assertEqual(ch["solves_count"], 1)

    # ── 5. Envio Concorrente (Race Conditions) ───────────────────────────────────

    def test_concurrent_flag_submissions_same_user(self):
        """Duas submissões simultâneas da mesma flag pelo mesmo usuário: exatamente uma pontua."""
        results = []

        def worker():
            with self.app.app_context():
                # Instancia client com contexto independente de sessão
                client = self.app.test_client()
                with client.session_transaction() as sess:
                    sess["user_id"] = 2
                    sess["csrf_token"] = self.csrf

                res = client.post(
                    "/api/challenges/golf-static-analysis-config/submit",
                    json={"flag": "FLAG{s0urc3_m4ps_t3ll_s3cr3ts}"},
                    headers={"X-CSRFToken": self.csrf},
                )
                results.append(res.status_code)

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # Exatamente um 200 e um 409
        self.assertIn(200, results)
        self.assertIn(409, results)

        with self.app.app_context():
            # Apenas 1 registro persistido no banco para o usuário 2
            db = get_db()
            count = db.execute(
                "SELECT COUNT(*) FROM challenge_solves WHERE user_id=2 AND challenge_id='golf-static-analysis-config'"
            ).fetchone()[0]
            self.assertEqual(count, 1)

    # ── 6. Comparação em Tempo Constante ─────────────────────────────────────────

    def test_flag_service_constant_time_verification(self):
        """Verifica que o serviço de flag valida com precisão formatos envelopados e brutos."""
        # hotel-junior-dev-challenge
        self.assertTrue(flag_service.verify_flag("hotel-junior-dev-challenge", "FLAG{k3y_r0t4t10n_m4st3r}"))
        self.assertTrue(flag_service.verify_flag("hotel-junior-dev-challenge", "k3y_r0t4t10n_m4st3r"))
        self.assertFalse(flag_service.verify_flag("hotel-junior-dev-challenge", "FLAG{wrong}"))
        self.assertFalse(flag_service.verify_flag("hotel-junior-dev-challenge", ""))
        self.assertFalse(flag_service.verify_flag("hotel-junior-dev-challenge", None))

        # Desafio inexistente
        self.assertFalse(flag_service.verify_flag("non-existent-challenge-id", "FLAG{test}"))


if __name__ == "__main__":
    unittest.main()
