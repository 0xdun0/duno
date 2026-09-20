"""tests/test_challenge_production.py — Testes de prontidão para produção controlada (Fase 5).

Cobre a Definition of Done da Fase 5:
- Feature flag CHALLENGES_ENABLED permite desligar todo o módulo sem novo deploy.
- Runbook de rollback testado e validado.
- Backup e restauração do registry e flags validados.
- Emissão de eventos estruturados em JSON e métricas de observabilidade.
"""
import unittest
import tempfile
import os
import shutil
import json
import sqlite3
from pathlib import Path

from app import create_app
from seed import DDL
from core.database import get_db
from modules.challenges.events import emit_event
from modules.challenges.backup import backup_registry, restore_registry, export_solves_data


class TestChallengeProduction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._orig_db = os.environ.get("DATABASE")
        cls._orig_enabled = os.environ.get("CHALLENGES_ENABLED")

        cls.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.db_path = cls.tmp_db.name
        cls.tmp_db.close()
        os.environ["DATABASE"] = cls.db_path

        conn = sqlite3.connect(cls.db_path)
        conn.executescript(DDL)
        conn.execute("INSERT INTO users (id, username, password_hash, role) VALUES (1, 'produser', 'hash', 'user')")
        conn.commit()
        conn.close()

        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["DATABASE"] = cls.db_path
        cls.app.config["SECRET_KEY"] = "test-secret-prod-12345"

    @classmethod
    def tearDownClass(cls):
        if cls._orig_db is not None:
            os.environ["DATABASE"] = cls._orig_db
        else:
            os.environ.pop("DATABASE", None)

        if cls._orig_enabled is not None:
            os.environ["CHALLENGES_ENABLED"] = cls._orig_enabled
        else:
            os.environ.pop("CHALLENGES_ENABLED", None)

        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)

    def setUp(self):
        self.client = self.app.test_client()
        self.csrf = "test-csrf-token-prod"

    # ── 1. Feature Flag Kill Switch (CHALLENGES_ENABLED) ─────────────────────────

    def test_feature_flag_disabled_blocks_all_challenge_routes(self):
        """Com CHALLENGES_ENABLED=false, rotas SSR retornam 404 e APIs retornam 503 imediatamente."""
        os.environ["CHALLENGES_ENABLED"] = "false"
        try:
            with self.client.session_transaction() as sess:
                sess["user_id"] = 1
                sess["csrf_token"] = self.csrf

            # Rota de catálogo retorna 404
            res_cat = self.client.get("/challenges")
            self.assertEqual(res_cat.status_code, 404)

            # Rota de detalhe retorna 404
            res_wt = self.client.get("/desafio/1")
            self.assertEqual(res_wt.status_code, 404)

            # API de start retorna 503
            res_api_start = self.client.post(
                "/api/challenges/hotel-junior-dev-challenge/instances",
                headers={"X-CSRFToken": self.csrf},
            )
            self.assertEqual(res_api_start.status_code, 503)
            data_start = res_api_start.get_json()
            self.assertEqual(data_start.get("status"), "disabled")

            # API de submit retorna 503
            res_api_sub = self.client.post(
                "/api/challenges/hotel-junior-dev-challenge/submit",
                json={"flag": "FLAG{k3y_r0t4t10n_m4st3r}"},
                headers={"X-CSRFToken": self.csrf},
            )
            self.assertEqual(res_api_sub.status_code, 503)
        finally:
            os.environ["CHALLENGES_ENABLED"] = "true"

    def test_feature_flag_hides_navbar_link(self):
        """Com CHALLENGES_ENABLED=false, o link CHALLENGES desaparece da barra de navegação."""
        os.environ["CHALLENGES_ENABLED"] = "false"
        try:
            with self.client.session_transaction() as sess:
                sess["user_id"] = 1

            res = self.client.get("/")
            self.assertNotIn("id=\"nav-challenges-link\"", res.get_data(as_text=True))
        finally:
            os.environ["CHALLENGES_ENABLED"] = "true"

    # ── 2. Observabilidade e Métricas ────────────────────────────────────────────

    def test_metrics_api_endpoint(self):
        """GET /api/challenges/metrics retorna estrutura consolidada para dashboards."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1

        res = self.client.get("/api/challenges/metrics")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        self.assertEqual(data.get("status"), "healthy")
        self.assertTrue(data.get("challenges_enabled"))
        self.assertIn("active_instances", data)
        self.assertIn("expired_instances", data)
        self.assertIn("failed_instances", data)
        self.assertIn("total_solves", data)
        self.assertIn("solves_by_challenge", data)

    def test_structured_event_logging_sanitizes_secrets(self):
        """emit_event gera payload padronizado e purga qualquer tentativa de logar segredos/flags."""
        event = emit_event(
            event_name="test_event",
            user_id=1,
            challenge_id="hotel-junior-dev-challenge",
            instance_id="uuid-1234",
            status="running",
            duration_ms=250,
            extra={
                "allowed_metric": 42,
                "flag": "FLAG{must_not_appear_in_log}",
                "token": "secret_token_val",
                "password": "pass",
            },
        )
        self.assertEqual(event["event"], "test_event")
        self.assertEqual(event["duration_ms"], 250)
        self.assertEqual(event["allowed_metric"], 42)

        # Garante sanitização de credenciais/chaves sensíveis
        self.assertNotIn("flag", event)
        self.assertNotIn("token", event)
        self.assertNotIn("password", event)

    # ── 3. Backup e Restauração do Catálogo / Flags ──────────────────────────────

    def test_backup_and_restore_registry_cycle(self):
        """Testa o ciclo completo de backup e restauração do catálogo e flags."""
        backup_tmp = tempfile.mkdtemp()
        try:
            info = backup_registry(backup_tmp)
            self.assertTrue(info["challenges_copied"])
            self.assertTrue(info["flags_copied"])
            self.assertTrue((Path(backup_tmp) / "challenges.yaml").exists())
            self.assertTrue((Path(backup_tmp) / "flags.yaml").exists())

            # Testa restauração
            restore_info = restore_registry(backup_tmp)
            self.assertTrue(restore_info["challenges_restored"])
            self.assertTrue(restore_info["flags_restored"])
        finally:
            shutil.rmtree(backup_tmp, ignore_errors=True)

    def test_export_solves_data(self):
        """Testa exportação lógica de dados de solves para migração/backup."""
        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT OR REPLACE INTO challenge_solves (id, challenge_id, user_id, points_awarded) VALUES ('s1', 'c1', 1, 100)"
            )
            db.commit()
            solves = export_solves_data(db)
            self.assertGreaterEqual(len(solves), 1)


if __name__ == "__main__":
    unittest.main()
