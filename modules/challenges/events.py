"""modules/challenges/events.py — Observabilidade e logs estruturados em JSON para o CTF.

Requisitos da Seção 23 do upgrade_v3.md:
- Emissão de eventos estruturados em JSON com campos padronizados:
  event, ts, user_id, challenge_id, instance_id, duration_ms, status.
- REGRA DE OURO DE SEGURANÇA: NUNCA registrar flags, tokens, senhas, cookies ou dados sensíveis.
"""
import json
import logging
import sys
from datetime import datetime, timezone

# Configura logger estruturado exclusivo para o subsistema CTF
logger = logging.getLogger("duno.ctf.events")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def emit_event(
    event_name: str,
    user_id=None,
    challenge_id: str = None,
    instance_id: str = None,
    status: str = None,
    duration_ms: int = None,
    extra: dict = None,
):
    """Emite um evento estruturado em formato JSON respeitando a Seção 23.1."""
    payload = {
        "event": event_name,
        "ts": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "challenge_id": challenge_id,
        "instance_id": instance_id,
        "status": status,
    }

    if duration_ms is not None:
        payload["duration_ms"] = int(duration_ms)

    if extra and isinstance(extra, dict):
        # Filtra chaves proibidas para garantir sanitização
        for k, v in extra.items():
            if k.lower() not in ("flag", "token", "runner_token", "password", "secret", "cookie", "auth"):
                payload[k] = v

    try:
        logger.info(json.dumps(payload))
    except Exception:
        pass

    return payload
