"""tests/test_challenge_runner.py — Testes do Challenge Runner, contrato HTTP, TTL, rate limit e isolamento."""
import os
import time
import json
import uuid
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path

from services.challenge_runner.runner_core import ChallengeRunnerCore, CPU_LIMIT, MEMORY_LIMIT, PIDS_LIMIT, CHALLENGE_NETWORK
from services.challenge_runner.app import app as runner_app, RUNNER_TOKEN
from modules.challenges.rate_limiter import rate_limiter


class TestChallengeRunner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["TESTING"] = "true"
        os.environ["RUNNER_DRY_RUN"] = "true"

    def setUp(self):
        from services.challenge_runner.app import runner
        runner.dry_run = True
        self.runner_core = ChallengeRunnerCore(dry_run=True)
        self.runner_client = runner_app.test_client()
        rate_limiter.reset_for_testing()

    # ── 1. Contrato HTTP do Runner (Seção 12) ───────────────────────────────────

    def test_healthz_public(self):
        """GET /healthz deve responder 200 sem necessidade de token."""
        res = self.runner_client.get("/healthz")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "ok")

    def test_runner_requires_token(self):
        """Endpoints /instances devem rejeitar chamadas sem X-Runner-Token (401)."""
        res_no_token = self.runner_client.post("/instances", json={})
        self.assertEqual(res_no_token.status_code, 401)

        res_bad_token = self.runner_client.post("/instances", headers={"X-Runner-Token": "wrong-token"}, json={})
        self.assertEqual(res_bad_token.status_code, 401)

    def test_start_instance_success(self):
        """POST /instances com token válido deve criar instância (201)."""
        inst_id = str(uuid.uuid4())
        payload = {
            "instance_id": inst_id,
            "challenge_id": "hotel-junior-dev-challenge",
            "user_id": 1,
            "ttl_seconds": 3600,
            "challenge_meta": {"internal_port": 3000},
        }
        res = self.runner_client.post(
            "/instances",
            headers={"X-Runner-Token": RUNNER_TOKEN},
            json=payload,
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["instance_id"], inst_id)
        self.assertIn("status", data)
        self.assertIn("expires_at", data)

    def test_idempotence_duplicate_post_rejected(self):
        """Dois POST /instances com mesmo instance_id devem retornar 409 sem duplicar."""
        inst_id = str(uuid.uuid4())
        payload = {
            "instance_id": inst_id,
            "challenge_id": "hotel-junior-dev-challenge",
            "user_id": 1,
            "ttl_seconds": 3600,
        }
        # Primeiro POST
        res1 = self.runner_client.post(
            "/instances",
            headers={"X-Runner-Token": RUNNER_TOKEN},
            json=payload,
        )
        self.assertIn(res1.status_code, (200, 201))

        # Segundo POST simultâneo com mesmo ID
        res2 = self.runner_client.post(
            "/instances",
            headers={"X-Runner-Token": RUNNER_TOKEN},
            json=payload,
        )
        self.assertEqual(res2.status_code, 409, "Idempotência violada: segundo POST deveria retornar 409.")

    def test_get_instance_status(self):
        """GET /instances/<id> retorna dados da instância."""
        inst_id = str(uuid.uuid4())
        payload = {
            "instance_id": inst_id,
            "challenge_id": "delta-idor-document-vault",
            "user_id": 1,
            "ttl_seconds": 1800,
        }
        self.runner_client.post(
            "/instances",
            headers={"X-Runner-Token": RUNNER_TOKEN},
            json=payload,
        )

        res = self.runner_client.get(
            f"/instances/{inst_id}",
            headers={"X-Runner-Token": RUNNER_TOKEN},
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["instance_id"], inst_id)
        self.assertEqual(data["challenge_id"], "delta-idor-document-vault")

    def test_delete_instance_success(self):
        """DELETE /instances/<id> encerra a instância (204)."""
        inst_id = str(uuid.uuid4())
        payload = {
            "instance_id": inst_id,
            "challenge_id": "delta-idor-document-vault",
            "user_id": 1,
            "ttl_seconds": 1800,
        }
        self.runner_client.post(
            "/instances",
            headers={"X-Runner-Token": RUNNER_TOKEN},
            json=payload,
        )

        res_del = self.runner_client.delete(
            f"/instances/{inst_id}",
            headers={"X-Runner-Token": RUNNER_TOKEN},
        )
        self.assertEqual(res_del.status_code, 204)

        # Após stop, status deve ser stopped
        res_st = self.runner_client.get(
            f"/instances/{inst_id}",
            headers={"X-Runner-Token": RUNNER_TOKEN},
        )
        self.assertEqual(res_st.get_json()["status"], "stopped")

    # ── 2. Limites de Recursos e Isolamento ───────────────────────────────────────

    def test_resource_limits_configured(self):
        """Verifica se os limites obrigatórios de CPU, Memória e PIDs estão ativos."""
        self.assertLessEqual(CPU_LIMIT, 1.0, "Limite de CPU deve ser restrito (<= 1.0 core).")
        self.assertIn("m", MEMORY_LIMIT.lower(), "Limite de memória deve ser restrito.")
        self.assertLessEqual(PIDS_LIMIT, 200, "Limite de PIDs deve ser restrito (<= 200).")
        self.assertEqual(CHALLENGE_NETWORK, "challenge-net")

    def test_web_app_does_not_mount_docker_sock(self):
        """Garante que docker-compose.yml NÃO monta o docker.sock no container web duno-app."""
        import yaml
        compose_path = Path(__file__).resolve().parent.parent / "docker-compose.yml"
        self.assertTrue(compose_path.exists())
        content = compose_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
        duno_app_volumes = data.get("services", {}).get("duno-app", {}).get("volumes", [])
        for vol in duno_app_volumes:
            self.assertNotIn("docker.sock", str(vol), "Risco Crítico: duno-app não deve montar /var/run/docker.sock")

    # ── 3. TTL e Limpeza Automática ──────────────────────────────────────────────

    def test_ttl_expiration_logic(self):
        """Verifica que instâncias com TTL vencido passam para status 'expired'."""
        inst_id = str(uuid.uuid4())
        # Cria instância com TTL de apenas 1 segundo
        ok, msg, code, inst = self.runner_core.start_instance(
            instance_id=inst_id,
            challenge_id="hotel-junior-dev-challenge",
            user_id=1,
            ttl_seconds=1,
        )
        self.assertTrue(ok)
        self.assertEqual(inst["status"], "running")

        # Força data de expiração no passado
        with self.runner_core._lock:
            past_dt = datetime.now(timezone.utc) - timedelta(seconds=10)
            self.runner_core._instances[inst_id]["expires_at"] = past_dt.isoformat()

        # Executa limpeza
        self.runner_core.cleanup_expired_instances()

        # Verifica que o status agora é 'expired'
        checked = self.runner_core.get_instance(inst_id)
        self.assertEqual(checked["status"], "expired")

    # ── 4. Rate Limiting ────────────────────────────────────────────────────────

    def test_rate_limiting_cooldown(self):
        """START subsequente antes do cooldown de 30s deve ser bloqueado com Retry-After."""
        user_id = 99
        client_ip = "192.168.1.50"

        # Primeiro start: permitido
        allowed, retry, _ = rate_limiter.check_rate_limit(user_id, "chal-1", client_ip)
        self.assertTrue(allowed)
        rate_limiter.record_start(user_id, client_ip)

        # Segundo start imediato: bloqueado
        allowed2, retry2, reason2 = rate_limiter.check_rate_limit(user_id, "chal-2", client_ip)
        self.assertFalse(allowed2)
        self.assertGreater(retry2, 0)
        self.assertIn("Aguarde", reason2)

    def test_build_failure_policy(self):
        """Três falhas consecutivas de build acionam política de maintenance."""
        cid = "faulty-challenge"
        self.assertFalse(self.runner_core.record_build_failure(cid))
        self.assertFalse(self.runner_core.record_build_failure(cid))
        # 3ª falha ativa o gatilho
        is_maintenance = self.runner_core.record_build_failure(cid)
        self.assertTrue(is_maintenance)
        self.assertEqual(self.runner_core.get_failure_count(cid), 3)


if __name__ == "__main__":
    unittest.main()
