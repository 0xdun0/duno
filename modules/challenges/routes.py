import os
import uuid
import secrets
from pathlib import Path
from datetime import datetime, timezone, timedelta
from flask import (
    Blueprint, render_template, abort, session, request,
    redirect, url_for, jsonify, make_response, send_file, current_app
)
from core.decorators import login_required
from core.auth import current_user
from core.database import get_db
from modules.challenges.catalog import catalog, get_challenge_walkthrough_path
from modules.challenges.rate_limiter import rate_limiter
from modules.challenges.runner_client import runner_client
from modules.challenges.solves_service import solves_service
from modules.challenges.events import emit_event

bp = Blueprint("challenges", __name__)


@bp.before_request
def check_challenges_enabled():
    """Feature flag CHALLENGES_ENABLED (Seção 24 — Fase 5). Desliga o módulo sem novo deploy."""
    val = os.environ.get("CHALLENGES_ENABLED", "true").strip().lower()
    if val not in ("true", "1", "yes", "on"):
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Módulo de desafios CTF temporariamente desativado.",
                "status": "disabled",
            }), 503
        abort(404)


def init_challenge_tables():
    """Garante a existência das tabelas de instâncias e solves no SQLite."""
    try:
        db = get_db()
        db.executescript("""
        CREATE TABLE IF NOT EXISTS challenge_instances (
            id TEXT PRIMARY KEY,
            challenge_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            container_ref TEXT,
            status TEXT NOT NULL CHECK(status IN ('starting','running','stopping','stopped','failed','expired')),
            endpoint TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            stopped_at TIMESTAMP,
            last_error TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS challenge_solves (
            id TEXT PRIMARY KEY,
            challenge_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            instance_id TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            points_awarded INTEGER NOT NULL,
            UNIQUE(user_id, challenge_id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(instance_id) REFERENCES challenge_instances(id)
        );

        CREATE INDEX IF NOT EXISTS idx_instances_user ON challenge_instances(user_id);
        CREATE INDEX IF NOT EXISTS idx_instances_challenge ON challenge_instances(challenge_id);
        CREATE INDEX IF NOT EXISTS idx_instances_status ON challenge_instances(status);
        CREATE INDEX IF NOT EXISTS idx_instances_expires ON challenge_instances(expires_at);
        CREATE INDEX IF NOT EXISTS idx_solves_user ON challenge_solves(user_id);
        """)
        db.commit()
    except Exception:
        pass


@bp.before_request
def ensure_setup():
    init_challenge_tables()
    # Gera token CSRF de sessão para requisições mutativas de desafios
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(24)


def verify_csrf():
    """Valida o token CSRF manual para operações mutativas POST."""
    expected = session.get("csrf_token")
    if not expected:
        return False
    # Checa header X-CSRFToken ou corpo JSON / Form
    received = request.headers.get("X-CSRFToken")
    if not received and request.is_json:
        received = (request.get_json(silent=True) or {}).get("csrf_token")
    if not received:
        received = request.form.get("csrf_token")
    return bool(received and secrets.compare_digest(received, expected))


# ── Páginas SSR ────────────────────────────────────────────────────────────────

@bp.route("/challenges", methods=["GET"])
@login_required
def index():
    """Catálogo oficial de desafios CTF."""
    try:
        current_app.jinja_env.auto_reload = True
        if current_app.jinja_env.cache:
            current_app.jinja_env.cache.clear()
    except Exception:
        pass
    user = current_user()
    challenges_list = catalog.list_available_for_user(user)
    return render_template("pages/challenges.html", challenges=challenges_list, csrf_token=session.get("csrf_token"))


@bp.route("/desafio/<identifier>", methods=["GET"])
@bp.route("/challenges/<identifier>", methods=["GET"])
@login_required
def challenge_page(identifier):
    """Página individual completa do desafio selecionado (ex: /desafio/1, /desafio/2)."""
    user = current_user()
    ch, idx = catalog.get_by_identifier(identifier, user=user)
    if not ch or ch.get("status") == "draft":
        abort(404)

    # Registra visualização para limpar o badge de "NOVA MÁQUINA"
    if user and ch:
        try:
            db = get_db()
            db.execute(
                "INSERT OR IGNORE INTO user_challenge_views (user_id, challenge_id) VALUES (?, ?)",
                (user["id"], ch["id"])
            )
            db.commit()
        except Exception:
            pass

    total_challenges = len(catalog.load_challenges())
    next_idx = idx + 1 if idx and idx < total_challenges else None
    prev_idx = idx - 1 if idx and idx > 1 else None
    return render_template(
        "pages/challenge_detail.html",
        challenge=ch,
        challenge_index=idx or 1,
        next_index=next_idx,
        prev_index=prev_idx,
        csrf_token=session.get("csrf_token"),
    )


@bp.route("/desafio/<identifier>/walkthrough", methods=["GET"])
@bp.route("/challenges/<identifier>/walkthrough", methods=["GET"])
@login_required
def challenge_walkthrough(identifier):
    """Página de walkthrough passo a passo do desafio."""
    user = current_user()
    ch, idx = catalog.get_by_identifier(identifier, user=user)
    if not ch or ch.get("status") == "draft":
        abort(404)

    # Walkthrough unificado: lê walkthrough.md da máquina, independente de ser community
    walkthrough_html = None
    wt_path = get_challenge_walkthrough_path(ch)
    if wt_path:
        try:
            import markdown as md_lib
            wt_text = wt_path.read_text(encoding="utf-8", errors="replace")
            walkthrough_html = md_lib.markdown(
                wt_text, extensions=["fenced_code", "tables", "toc"]
            )
        except Exception:
            pass
    elif not ch.get("has_walkthrough"):
        abort(404)
    exp_val = ch.get("expires_at")
    if hasattr(exp_val, "isoformat"):
        ch["expires_at_iso"] = exp_val.isoformat()
    elif isinstance(exp_val, str) and " " in exp_val:
        ch["expires_at_iso"] = exp_val.replace(" ", "T")
    else:
        ch["expires_at_iso"] = str(exp_val) if exp_val else ""

    return render_template(
        "pages/walkthrough.html",
        challenge=ch,
        challenge_index=idx or 1,
        csrf_token=session.get("csrf_token"),
        walkthrough_html=walkthrough_html,
    )


# ── API REST (Contrato do Runner e Polling) ───────────────────────────────────

@bp.route("/api/challenges/<challenge_id>/instances", methods=["POST"])
@login_required
def api_start_instance(challenge_id):
    """Inicia uma instância isolada para o desafio selecionado com rate limiting e CSRF."""
    if not verify_csrf():
        return jsonify({"error": "Forbidden: Token CSRF inválido ou ausente"}), 403

    ch = catalog.get_by_id(challenge_id)
    if not ch or ch.get("status") != "available":
        return jsonify({"error": "Desafio não encontrado ou indisponível"}), 404

    user = current_user()
    user_id = user["id"]
    client_ip = request.remote_addr or "127.0.0.1"

    # Aplica rate limiting rígido (Seção 11.1)
    allowed, retry_after, reason = rate_limiter.check_rate_limit(user_id, challenge_id, client_ip)
    if not allowed:
        emit_event("challenge_rate_limited", user_id=user_id, challenge_id=challenge_id, extra={"retry_after": retry_after, "reason": reason})
        resp = make_response(jsonify({"error": reason}), 429)
        resp.headers["Retry-After"] = str(retry_after)
        return resp

    emit_event("challenge_start_requested", user_id=user_id, challenge_id=challenge_id)

    # Gera UUID seguro no servidor
    instance_id = str(uuid.uuid4())
    ttl_seconds = 3600

    # Invoca Challenge Runner
    code, result = runner_client.start_instance(
        instance_id=instance_id,
        challenge_id=challenge_id,
        user_id=user_id,
        ttl_seconds=ttl_seconds,
        challenge_meta=ch,
    )

    if code not in (200, 201):
        emit_event("challenge_start_failed", user_id=user_id, challenge_id=challenge_id, status="failed")
        err_msg = result.get("error", "Falha ao iniciar o container do laboratório")
        return jsonify({"error": err_msg}), code

    emit_event("challenge_started", user_id=user_id, challenge_id=challenge_id, instance_id=instance_id, status="starting")


    # Registra no rate limiter e persiste no SQLite
    rate_limiter.record_start(user_id, client_ip)

    expires_at_raw = result.get("expires_at")
    if expires_at_raw:
        try:
            exp_dt = datetime.fromisoformat(str(expires_at_raw).replace("Z", "+00:00"))
        except Exception:
            exp_dt = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    else:
        exp_dt = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)

    # SQLite TIMESTAMP converter (PARSE_DECLTYPES) requer separador espaço "YYYY-MM-DD HH:MM:SS"
    db_expires_at = exp_dt.strftime("%Y-%m-%d %H:%M:%S")
    iso_expires_at = exp_dt.isoformat()

    try:
        db = get_db()
        db.execute(
            """INSERT INTO challenge_instances (id, challenge_id, user_id, container_ref, status, endpoint, expires_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                instance_id,
                challenge_id,
                user_id,
                f"duno-ctf-{challenge_id[:16]}-{instance_id[:8]}",
                result.get("status", "starting"),
                result.get("endpoint"),
                db_expires_at,
            ),
        )
        db.commit()
    except Exception:
        pass

    return jsonify({
        "instance_id": instance_id,
        "status": result.get("status", "starting"),
        "endpoint": result.get("endpoint"),
        "expires_at": iso_expires_at,
    }), 201


@bp.route("/api/challenge-instances/<instance_id>", methods=["GET"])
@login_required
def api_get_instance(instance_id):
    """Consulta de status de instância para polling do frontend."""
    user = current_user()
    user_id = user["id"]

    db = get_db()
    row = db.execute(
        "SELECT * FROM challenge_instances WHERE id=?", (instance_id,)
    ).fetchone()

    if not row:
        return jsonify({"error": "Instância não encontrada"}), 404

    # Segurança: somente o dono ou admin pode consultar
    if row["user_id"] != user_id and user.get("role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403

    # Se ainda estiver em starting/running, consulta runner para atualizar status
    cur_status = row["status"]
    endpoint = row["endpoint"]

    if cur_status in ("starting", "running"):
        code, runner_data = runner_client.get_instance_status(instance_id)
        if code == 200 and runner_data:
            new_status = runner_data.get("status", cur_status)
            new_endpoint = runner_data.get("endpoint", endpoint)
            if new_status != cur_status or new_endpoint != endpoint:
                db.execute(
                    "UPDATE challenge_instances SET status=?, endpoint=? WHERE id=?",
                    (new_status, new_endpoint, instance_id),
                )
                db.commit()
                cur_status = new_status
                endpoint = new_endpoint

    exp_val = row["expires_at"]
    if hasattr(exp_val, "isoformat"):
        exp_str = exp_val.isoformat()
    elif isinstance(exp_val, str) and " " in exp_val:
        exp_str = exp_val.replace(" ", "T")
    else:
        exp_str = str(exp_val) if exp_val else None

    return jsonify({
        "instance_id": instance_id,
        "challenge_id": row["challenge_id"],
        "status": cur_status,
        "endpoint": endpoint,
        "expires_at": exp_str,
        "last_error": row["last_error"],
    }), 200


@bp.route("/api/challenge-instances/<instance_id>/stop", methods=["POST"])
@login_required
def api_stop_instance(instance_id):
    """Para uma instância ativa."""
    if not verify_csrf():
        return jsonify({"error": "Forbidden: Token CSRF inválido ou ausente"}), 403

    user = current_user()
    user_id = user["id"]

    db = get_db()
    row = db.execute(
        "SELECT * FROM challenge_instances WHERE id=?", (instance_id,)
    ).fetchone()

    if not row:
        return jsonify({"error": "Instância não encontrada"}), 404

    if row["user_id"] != user_id and user.get("role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403

    # Solicita parada ao runner
    runner_client.stop_instance(instance_id)

    db.execute(
        "UPDATE challenge_instances SET status='stopped', stopped_at=CURRENT_TIMESTAMP WHERE id=?",
        (instance_id,),
    )
    db.commit()

    emit_event("challenge_stopped", user_id=user_id, instance_id=instance_id, status="stopped")

    return jsonify({"status": "stopped", "instance_id": instance_id}), 200


@bp.route("/api/challenge-instances/<instance_id>/renew", methods=["POST"])
@login_required
def api_renew_instance(instance_id):
    """Renova o tempo da instância ativa (+1 hora)."""
    if not verify_csrf():
        return jsonify({"error": "Forbidden: Token CSRF inválido ou ausente"}), 403

    user = current_user()
    user_id = user["id"]

    db = get_db()
    row = db.execute(
        "SELECT * FROM challenge_instances WHERE id=?", (instance_id,)
    ).fetchone()

    if not row:
        return jsonify({"error": "Instância não encontrada"}), 404

    if row["user_id"] != user_id and user.get("role") != "admin":
        return jsonify({"error": "Acesso negado"}), 403

    if row["status"] not in ("starting", "running"):
        return jsonify({"error": "Apenas instâncias ativas podem ter o tempo renovado."}), 400

    # Solicita extensão ao runner
    runner_client.extend_instance(instance_id, additional_seconds=3600)

    # Calcula nova expiração (+1 hora)
    now = datetime.now(timezone.utc)
    cur_exp = row["expires_at"]
    if isinstance(cur_exp, str):
        try:
            exp_dt = datetime.fromisoformat(cur_exp.replace("Z", "+00:00"))
        except Exception:
            exp_dt = now
    elif hasattr(cur_exp, "isoformat"):
        exp_dt = cur_exp
    else:
        exp_dt = now

    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

    base_dt = max(exp_dt, now)
    new_exp_dt = base_dt + timedelta(seconds=3600)
    db_expires_at = new_exp_dt.strftime("%Y-%m-%d %H:%M:%S")

    db.execute(
        "UPDATE challenge_instances SET expires_at=? WHERE id=?",
        (db_expires_at, instance_id),
    )
    db.commit()

    return jsonify({
        "status": "success",
        "instance_id": instance_id,
        "expires_at": new_exp_dt.isoformat(),
        "message": "Tempo renovado com sucesso (+1h)",
    }), 200


@bp.route("/api/challenges/<challenge_id>/submit", methods=["POST"])
@login_required
def api_submit_flag(challenge_id):
    """Submete uma flag para validação server-side com proteção CSRF e tempo constante."""
    if not verify_csrf():
        return jsonify({"error": "Forbidden: Token CSRF inválido ou ausente"}), 403

    user = current_user()
    user_id = user["id"]

    data = request.get_json(silent=True) or {}
    flag = data.get("flag", "")
    if not isinstance(flag, str) or not flag.strip():
        return jsonify({"error": "O campo 'flag' é obrigatório"}), 400

    client_ip = request.remote_addr or "127.0.0.1"
    success, status, points, message = solves_service.submit_flag(
        user_id=user_id,
        challenge_id=challenge_id,
        flag=flag,
        ip=client_ip,
    )

    emit_event(
        "flag_submitted",
        user_id=user_id,
        challenge_id=challenge_id,
        status=status,
        extra={"points": points, "success": success},
    )

    if status == "not_found":
        return jsonify({"error": message}), 404
    elif status == "already_solved":
        return jsonify({
            "error": message,
            "already_solved": True,
            "points_awarded": 0,
        }), 409
    elif status == "invalid_flag":
        return jsonify({"error": message}), 400
    elif success:
        return jsonify({
            "success": True,
            "message": message,
            "points_awarded": points,
            "already_solved": False,
        }), 200

    return jsonify({"error": "Erro interno ao processar submissão"}), 500


@bp.route("/api/challenges/metrics", methods=["GET"])
@login_required
def api_challenges_metrics():
    """Retorna métricas consolidadas do subsistema CTF para observabilidade (Seção 23)."""
    db = get_db()
    try:
        active_cnt = db.execute(
            "SELECT COUNT(*) FROM challenge_instances WHERE status IN ('starting', 'running')"
        ).fetchone()[0]
        expired_cnt = db.execute(
            "SELECT COUNT(*) FROM challenge_instances WHERE status='expired'"
        ).fetchone()[0]
        failed_cnt = db.execute(
            "SELECT COUNT(*) FROM challenge_instances WHERE status='failed'"
        ).fetchone()[0]
        total_solves = db.execute(
            "SELECT COUNT(*) FROM challenge_solves"
        ).fetchone()[0]
        solves_by_ch = {}
        for r in db.execute("SELECT challenge_id, COUNT(*) as c FROM challenge_solves GROUP BY challenge_id").fetchall():
            solves_by_ch[r["challenge_id"]] = r["c"]
    except Exception:
        active_cnt = expired_cnt = failed_cnt = total_solves = 0
        solves_by_ch = {}

    enabled = os.environ.get("CHALLENGES_ENABLED", "true").strip().lower() in ("true", "1", "yes", "on")
    return jsonify({
        "status": "healthy",
        "challenges_enabled": enabled,
        "active_instances": active_cnt,
        "expired_instances": expired_cnt,
        "failed_instances": failed_cnt,
        "total_solves": total_solves,
        "solves_by_challenge": solves_by_ch,
    }), 200


