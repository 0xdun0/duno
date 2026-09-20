"""modules/challenges/flag_service.py — Mecanismo de validação de flag em tempo constante.

Requisitos da Seção 18 do upgrade_v3.md:
- Validação server-side.
- Comparação em tempo constante (secrets.compare_digest) para evitar timing attacks.
- Mensagens de erro nunca revelam a flag correta nem pistas.
"""
import os
import secrets
from pathlib import Path
import yaml

BASE_DIR = Path(__file__).resolve().parent.parent.parent
FLAGS_PATH = BASE_DIR / "data" / "flags.yaml"


class FlagService:
    """Gerencia e valida flags de desafios com proteção contra timing attacks."""

    def __init__(self, flags_path=None):
        self.flags_path = Path(flags_path) if flags_path else FLAGS_PATH
        self._cache = {}
        self._last_mtime = 0

    def _load_flags(self):
        if not self.flags_path.exists():
            return {}

        try:
            mtime = self.flags_path.stat().st_mtime
            if mtime != self._last_mtime or not self._cache:
                with open(self.flags_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                if isinstance(data, dict):
                    self._cache = data
                    self._last_mtime = mtime
        except Exception:
            pass

        return self._cache

    def get_flags_for_challenge(self, challenge_id: str) -> list:
        flags_map = self._load_flags()
        val = flags_map.get(challenge_id, [])
        if isinstance(val, str):
            return [val]
        elif isinstance(val, list):
            return [str(item) for item in val]
        return []

    def verify_flag(self, challenge_id: str, submitted_flag: str) -> bool:
        """Compara a flag submetida contra as flags autorizadas em tempo constante.
        
        Suporta comparação idêntica e sem casing/formatação FLAG{...} de forma segura.
        """
        if not submitted_flag or not isinstance(submitted_flag, str):
            return False

        submitted = submitted_flag.strip()
        # Limite razoável para prevenir DoS por payload gigantesco
        if len(submitted) > 256:
            return False

        valid_flags = self.get_flags_for_challenge(challenge_id)
        if not valid_flags:
            return False

        matched = False
        for target in valid_flags:
            target_clean = target.strip()
            # Comparação em tempo constante
            if secrets.compare_digest(submitted, target_clean):
                matched = True

            # Normalização de prefixo FLAG{...} se o usuário enviar sem ou com o wrapper
            if target_clean.startswith("FLAG{") and target_clean.endswith("}"):
                inner = target_clean[5:-1]
                if secrets.compare_digest(submitted, inner):
                    matched = True
            elif not target_clean.startswith("FLAG{"):
                wrapped = f"FLAG{{{target_clean}}}"
                if secrets.compare_digest(submitted, wrapped):
                    matched = True

        return matched


flag_service = FlagService()
