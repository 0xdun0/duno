"""modules/challenges/solves_service.py — Gerenciamento de submissão e pontuação de flags CTF.

Requisitos da Seção 18 do upgrade_v3.md:
- Validação server-side.
- Solve idempotente (não pontuar duas vezes o mesmo usuário/desafio).
- Pontuação baseada no registry (catalog), nunca enviada pelo cliente.
- Nunca revelar a flag correta em mensagens de erro.
- Registrar data, usuário e instância de cada submissão.
- Atualizar solves_count somente após sucesso real.
"""
import uuid
import sqlite3
from core.database import get_db
from modules.challenges.catalog import catalog
from modules.challenges.flag_service import flag_service


class SolvesService:
    """Serviço para registro e consulta de soluções de desafios CTF."""

    def has_user_solved(self, user_id: int, challenge_id: str) -> bool:
        """Verifica se o usuário já pontuou neste desafio."""
        db = get_db()
        row = db.execute(
            "SELECT 1 FROM challenge_solves WHERE user_id=? AND challenge_id=?",
            (user_id, challenge_id),
        ).fetchone()
        return row is not None

    def get_user_total_points(self, user_id: int) -> int:
        """Calcula o total de pontos acumulados pelo usuário nos desafios CTF."""
        db = get_db()
        row = db.execute(
            "SELECT COALESCE(SUM(points_awarded), 0) as total FROM challenge_solves WHERE user_id=?",
            (user_id,),
        ).fetchone()
        return int(row["total"]) if row else 0

    def get_challenge_solves_count(self, challenge_id: str) -> int:
        """Retorna o número de usuários únicos que solucionaram o desafio."""
        db = get_db()
        row = db.execute(
            "SELECT COUNT(DISTINCT user_id) as cnt FROM challenge_solves WHERE challenge_id=?",
            (challenge_id,),
        ).fetchone()
        return int(row["cnt"]) if row else 0

    def submit_flag(self, user_id: int, challenge_id: str, flag: str, ip: str = None) -> tuple:
        """Submete uma flag e processa a pontuação de forma atômica e idempotente.
        
        Retorna: (success: bool, status: str, points: int, message: str)
        Status possíveis:
          - "solved": Flag correta e pontuação registrada
          - "already_solved": Desafio já resolvido anteriormente por este usuário
          - "invalid_flag": Flag incorreta (sem pistas reveladas)
          - "not_found": Desafio não existe no catálogo
        """
        ch = catalog.get_by_id(challenge_id)
        if not ch:
            return False, "not_found", 0, "Desafio não encontrado."

        db = get_db()

        # 1. Verifica se já foi solucionado anteriormente
        if self.has_user_solved(user_id, challenge_id):
            return False, "already_solved", 0, "Desafio já solucionado por este usuário."

        # 2. Valida a flag em tempo constante
        if not flag_service.verify_flag(challenge_id, flag):
            return False, "invalid_flag", 0, "Flag incorreta. Tente novamente."

        # 3. Pontuação obtida exclusivamente do catálogo (registry)
        points = int(ch.get("points", 0))

        # 4. Obtém instância associada se houver
        instance_id = None
        try:
            inst_row = db.execute(
                """SELECT id FROM challenge_instances
                   WHERE user_id=? AND challenge_id=?
                   ORDER BY started_at DESC LIMIT 1""",
                (user_id, challenge_id),
            ).fetchone()
            if inst_row:
                instance_id = inst_row["id"]
        except Exception:
            pass

        # 5. Inserção atômica com garantia UNIQUE(user_id, challenge_id)
        solve_id = str(uuid.uuid4())
        try:
            db.execute(
                """INSERT INTO challenge_solves (id, challenge_id, user_id, instance_id, points_awarded)
                   VALUES (?, ?, ?, ?, ?)""",
                (solve_id, challenge_id, user_id, instance_id, points),
            )
            # Opcional: registrar em audit_log se tabela existir
            try:
                db.execute(
                    "INSERT INTO audit_log (user_id, action, ip) VALUES (?, ?, ?)",
                    (user_id, f"challenge_solve:{challenge_id}", ip or "unknown"),
                )
            except Exception:
                pass

            db.commit()
        except sqlite3.IntegrityError:
            # Em caso de corrida concorrente, o constraint UNIQUE previne duplicidade
            return False, "already_solved", 0, "Desafio já solucionado por este usuário."

        return True, "solved", points, "Parabéns! Flag correta!"


solves_service = SolvesService()
