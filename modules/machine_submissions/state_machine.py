"""modules/machine_submissions/state_machine.py — Regras e transições da Máquina de Estados de Submissões."""
import sqlite3
from datetime import datetime
from modules.machine_submissions.db import log_machine_audit

VALID_STATES = (
    "DRAFT",
    "SUBMITTED",
    "TRIAGE",
    "BUILDING",
    "SECURITY_REVIEW",
    "FUNCTIONAL_TEST",
    "CONTENT_REVIEW",
    "APPROVED",
    "PUBLISHED",
    "CHANGES_REQUESTED",
    "REJECTED",
    "UNPUBLISHED",
    "ARCHIVED"
)

# Mapa de transições permitidas (Regra §42 do plano)
ALLOWED_TRANSITIONS = {
    "DRAFT": {"SUBMITTED", "ARCHIVED"},
    "SUBMITTED": {"TRIAGE", "BUILDING", "SECURITY_REVIEW", "CHANGES_REQUESTED", "REJECTED", "APPROVED", "PUBLISHED"},
    "TRIAGE": {"BUILDING", "SECURITY_REVIEW", "FUNCTIONAL_TEST", "CHANGES_REQUESTED", "REJECTED", "APPROVED", "PUBLISHED"},
    "BUILDING": {"SECURITY_REVIEW", "FUNCTIONAL_TEST", "CHANGES_REQUESTED", "TRIAGE", "REJECTED", "APPROVED", "PUBLISHED"},
    "SECURITY_REVIEW": {"FUNCTIONAL_TEST", "CONTENT_REVIEW", "CHANGES_REQUESTED", "REJECTED", "APPROVED", "PUBLISHED"},
    "FUNCTIONAL_TEST": {"CONTENT_REVIEW", "APPROVED", "PUBLISHED", "CHANGES_REQUESTED", "SECURITY_REVIEW", "REJECTED"},
    "CONTENT_REVIEW": {"APPROVED", "PUBLISHED", "CHANGES_REQUESTED", "FUNCTIONAL_TEST", "REJECTED"},
    "APPROVED": {"PUBLISHED", "CHANGES_REQUESTED", "UNPUBLISHED"},
    "CHANGES_REQUESTED": {"SUBMITTED", "BUILDING", "TRIAGE", "REJECTED"},
    "REJECTED": {"TRIAGE", "DRAFT"},
    "PUBLISHED": {"UNPUBLISHED", "ARCHIVED"},
    "UNPUBLISHED": {"PUBLISHED", "ARCHIVED", "CONTENT_REVIEW"},
    "ARCHIVED": {"UNPUBLISHED"}
}


class StateTransitionError(Exception):
    """Exceção levantada quando uma transição de estado é inválida."""
    pass


def can_transition(from_state: str, to_state: str) -> bool:
    """Verifica se uma transição de estado é formalmente permitida."""
    if from_state == to_state:
        return True
    allowed = ALLOWED_TRANSITIONS.get(from_state, set())
    return to_state in allowed


def transition_submission(db: sqlite3.Connection, submission_id: int, to_state: str, changed_by_user_id: int, reason: str | None = None, ip: str | None = None) -> str:
    """Aplica uma transição de estado na submissão, gravando histórico e auditoria."""
    sub = db.execute("SELECT id, status FROM machine_submissions WHERE id = ?", (submission_id,)).fetchone()
    if not sub:
        raise StateTransitionError(f"Submissão {submission_id} não encontrada.")

    from_state = sub["status"]
    if from_state != to_state and not can_transition(from_state, to_state):
        raise StateTransitionError(f"Transição de {from_state} para {to_state} não é permitida.")

    published_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S") if to_state == "PUBLISHED" else None

    # Atualiza cabeçalho da submissão
    if published_at:
        db.execute(
            """UPDATE machine_submissions 
               SET status = ?, updated_at = CURRENT_TIMESTAMP, published_at = ? 
               WHERE id = ?""",
            (to_state, published_at, submission_id)
        )
    else:
        db.execute(
            """UPDATE machine_submissions 
               SET status = ?, updated_at = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (to_state, submission_id)
        )

    # Grava no histórico de transições
    db.execute(
        """INSERT INTO machine_status_history (submission_id, from_status, to_status, changed_by_user_id, reason)
           VALUES (?, ?, ?, ?, ?)""",
        (submission_id, from_state, to_state, changed_by_user_id, reason or f"Transição para {to_state}")
    )

    # Grava auditoria
    log_machine_audit(
        db,
        user_id=changed_by_user_id,
        action=f"STATE_TRANSITION_{to_state}",
        resource="machine_submissions",
        resource_id=str(submission_id),
        status="SUCCESS",
        ip=ip,
        metadata={"from_status": from_state, "to_status": to_state, "reason": reason}
    )

    db.commit()
    return to_state
