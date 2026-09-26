"""modules/challenges/runner_client.py — Cliente HTTP para comunicação do DUNO Web com o Challenge Runner."""
import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

RUNNER_URL = os.environ.get("CHALLENGE_RUNNER_URL", "http://127.0.0.1:9000")
RUNNER_TOKEN = os.environ.get("CHALLENGE_RUNNER_TOKEN", "duno-runner-secret-key")


class ChallengeRunnerClient:
    """Encapsula as chamadas HTTP para o Challenge Runner."""

    def __init__(self, base_url=None, token=None):
        self.base_url = (base_url or RUNNER_URL).rstrip("/")
        self.token = token or RUNNER_TOKEN

    def _request(self, method, path, data=None, timeout=120):
        url = f"{self.base_url}{path}"
        headers = {
            "X-Runner-Token": self.token,
            "Content-Type": "application/json",
            "User-Agent": "DUNO-Web/1.0",
        }

        def _json_serial(obj):
            if hasattr(obj, "isoformat"):
                return obj.isoformat()
            return str(obj)

        req_body = json.dumps(data, default=_json_serial).encode("utf-8") if data is not None else None
        req = urllib.request.Request(url, data=req_body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = resp.status
                if status == 204:
                    return status, {}
                body = resp.read().decode("utf-8")
                return status, json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            if e.code == 401:
                return self._fallback_local(method, path, data, "Runner token mismatch")
            err_body = e.read().decode("utf-8")
            try:
                parsed = json.loads(err_body)
            except Exception:
                parsed = {"error": str(e)}
            return e.code, parsed
        except Exception as e:
            # Fallback direto em memória se o runner estiver embutido / mock de teste
            return self._fallback_local(method, path, data, str(e))

    def _fallback_local(self, method, path, data, original_err):
        """Fallback local quando o container do runner não estiver ativo ou em ambiente de teste."""
        try:
            from services.challenge_runner.runner_core import ChallengeRunnerCore
            global _local_runner_singleton
            if "_local_runner_singleton" not in globals():
                _local_runner_singleton = ChallengeRunnerCore(dry_run=True)

            if method == "POST" and path == "/instances":
                ok, msg, code, inst = _local_runner_singleton.start_instance(
                    instance_id=data["instance_id"],
                    challenge_id=data["challenge_id"],
                    user_id=data["user_id"],
                    ttl_seconds=data.get("ttl_seconds", 3600),
                    challenge_meta=data.get("challenge_meta"),
                )
                return code, inst
            elif method == "GET" and path.startswith("/instances/"):
                iid = path.replace("/instances/", "")
                inst = _local_runner_singleton.get_instance(iid)
                return (200, inst) if inst else (404, {"error": "Not found"})
            elif method == "DELETE" and path.startswith("/instances/"):
                iid = path.replace("/instances/", "")
                ok, msg, code = _local_runner_singleton.stop_instance(iid)
                return code, {}
            elif method == "POST" and "/extend" in path:
                iid = path.split("/")[2]
                secs = data.get("additional_seconds", 3600) if data else 3600
                ok, exp, code = _local_runner_singleton.extend_instance(iid, additional_seconds=secs)
                return (code, {"instance_id": iid, "expires_at": exp}) if ok else (code, {"error": exp})
        except Exception:
            pass
        return 503, {"error": f"Challenge Runner indisponível: {original_err}"}

    def start_instance(self, instance_id, challenge_id, user_id, ttl_seconds=3600, challenge_meta=None):
        payload = {
            "instance_id": instance_id,
            "challenge_id": challenge_id,
            "user_id": user_id,
            "ttl_seconds": ttl_seconds,
            "challenge_meta": challenge_meta,
        }
        return self._request("POST", "/instances", payload)

    def get_instance_status(self, instance_id):
        return self._request("GET", f"/instances/{instance_id}")

    def stop_instance(self, instance_id):
        return self._request("DELETE", f"/instances/{instance_id}", timeout=6)

    def extend_instance(self, instance_id, additional_seconds=3600):
        return self._request("POST", f"/instances/{instance_id}/extend", {"additional_seconds": additional_seconds})


runner_client = ChallengeRunnerClient()
