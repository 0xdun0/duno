"""modules/challenges/rate_limiter.py — Rate Limiting obrigatório para START de instâncias (Seção 11.1)."""
import time
import threading
from datetime import datetime, timezone
from core.database import get_db

# Limites da especificação
MAX_ACTIVE_PER_CHALLENGE = 1
MAX_ACTIVE_TOTAL_PER_USER = 3
START_COOLDOWN_SECONDS = 30
MAX_STARTS_PER_MIN_IP = 3
MAX_STARTS_PER_HOUR_USER = 20


class ChallengeRateLimiter:

    def __init__(self):
        self._lock = threading.Lock()
        self._user_last_start = {}      # user_id -> timestamp
        self._ip_starts = {}            # ip -> list of timestamps
        self._user_hourly_starts = {}   # user_id -> list of timestamps

    def check_rate_limit(self, user_id, challenge_id, client_ip):
        """
        Aplica todos os 5 critérios de limitação da Seção 11.1.
        Retorna (allowed: bool, retry_after: int, reason: str).
        """
        now = time.time()

        with self._lock:
            # 1. Cooldown de 30s entre STARTs do mesmo usuário
            last_start = self._user_last_start.get(user_id, 0)
            elapsed_cooldown = now - last_start
            if elapsed_cooldown < START_COOLDOWN_SECONDS:
                retry_after = int(START_COOLDOWN_SECONDS - elapsed_cooldown) + 1
                return False, retry_after, f"Aguarde {retry_after}s antes de iniciar outro desafio."

            # 2. STARTs por minuto por IP (máx 3/min)
            ip_times = [t for t in self._ip_starts.get(client_ip, []) if now - t <= 60]
            self._ip_starts[client_ip] = ip_times
            if len(ip_times) >= MAX_STARTS_PER_MIN_IP:
                oldest = ip_times[0]
                retry_after = int(60 - (now - oldest)) + 1
                return False, retry_after, "Muitas requisições deste IP. Aguarde um minuto."

            # 3. STARTs por hora por usuário (máx 20/h)
            user_times = [t for t in self._user_hourly_starts.get(user_id, []) if now - t <= 3600]
            self._user_hourly_starts[user_id] = user_times
            if len(user_times) >= MAX_STARTS_PER_HOUR_USER:
                oldest = user_times[0]
                retry_after = int(3600 - (now - oldest)) + 1
                return False, retry_after, "Limite horário de inicializações atingido (20/hora)."

        # 4 & 5. Checagens no banco de dados de instâncias ativas
        try:
            db = get_db()
            # 4. Instâncias ativas do usuário para este desafio específico (máx 1)
            row_chal = db.execute(
                """SELECT COUNT(*) as count FROM challenge_instances
                   WHERE user_id=? AND challenge_id=? AND status IN ('starting', 'running')""",
                (user_id, challenge_id),
            ).fetchone()
            if row_chal and row_chal["count"] >= MAX_ACTIVE_PER_CHALLENGE:
                return False, 30, "Você já possui uma instância ativa para este desafio."

            # 5. Instâncias ativas totais por usuário (máx 3)
            row_total = db.execute(
                """SELECT COUNT(*) as count FROM challenge_instances
                   WHERE user_id=? AND status IN ('starting', 'running')""",
                (user_id,),
            ).fetchone()
            if row_total and row_total["count"] >= MAX_ACTIVE_TOTAL_PER_USER:
                return False, 60, "Você atingiu o limite de 3 instâncias ativas simultâneas."
        except Exception:
            pass

        return True, 0, None

    def record_start(self, user_id, client_ip):
        """Registra o timestamp do START aprovado."""
        now = time.time()
        with self._lock:
            self._user_last_start[user_id] = now
            self._ip_starts.setdefault(client_ip, []).append(now)
            self._user_hourly_starts.setdefault(user_id, []).append(now)

    def reset_for_testing(self):
        """Limpa registros em memória (para testes unitários)."""
        with self._lock:
            self._user_last_start.clear()
            self._ip_starts.clear()
            self._user_hourly_starts.clear()


rate_limiter = ChallengeRateLimiter()
