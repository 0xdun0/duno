"""modules/machine_submissions/admin_routes.py — Painel Administrativo, Review de Máquinas e Auditoria."""
import os
import json
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from core.decorators import admin_required, login_required
from core.auth import current_user
from core.database import get_db
from modules.machine_submissions.db import init_submissions_db, log_machine_audit
from modules.machine_submissions.state_machine import transition_submission, StateTransitionError
from modules.machine_submissions.worker import run_build_job, run_scan_job, run_test_job, cleanup_machine_job

admin_bp = Blueprint("submissions_admin", __name__)


@admin_bp.before_request
def ensure_admin():
    db = get_db()
    init_submissions_db(db)


# ══════════════════════════════════════════════════════════════════════════════
# 1. TELAS ADMINISTRATIVAS
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route("/admin")
@admin_required
def admin_dashboard():
    """Dashboard Administrativo global com indicadores de máquinas e segurança."""
    user = current_user()
    db = get_db()

    # Contagem de submissões por status
    counts = dict(db.execute(
        """SELECT status, COUNT(*) as total 
           FROM machine_submissions 
           GROUP BY status"""
    ).fetchall())

    pending_review = counts.get("SUBMITTED", 0) + counts.get("TRIAGE", 0)
    building = counts.get("BUILDING", 0)
    security_review = counts.get("SECURITY_REVIEW", 0)
    published = counts.get("PUBLISHED", 0)
    changes_requested = counts.get("CHANGES_REQUESTED", 0)

    # Findings de segurança
    finding_counts = dict(db.execute(
        """SELECT severity, COUNT(*) as total
           FROM machine_findings
           WHERE status = 'open'
           GROUP BY severity"""
    ).fetchall())

    # Máquinas recentes
    recent_submissions = db.execute(
        """SELECT s.id, s.slug, s.name, s.status, s.current_version, s.updated_at, u.username as author_name,
                  m.os_type, m.author_difficulty, m.category
           FROM machine_submissions s
           JOIN users u ON u.id = s.user_id
           LEFT JOIN machine_metadata m ON m.submission_id = s.id AND m.version_id = (
               SELECT id FROM machine_versions v WHERE v.submission_id = s.id ORDER BY v.id DESC LIMIT 1
           )
           ORDER BY s.updated_at DESC LIMIT 8"""
    ).fetchall()

    return render_template(
        "admin/dashboard.html",
        pending_review=pending_review,
        building=building,
        security_review=security_review,
        published=published,
        changes_requested=changes_requested,
        finding_counts=finding_counts,
        recent_submissions=recent_submissions,
        user=user
    )


@admin_bp.route("/admin/machines")
@admin_required
def machines_list():
    """Lista de Máquinas e Submissões com filtros por status, dificuldade, OS e categoria."""
    user = current_user()
    db = get_db()

    status_filter = request.args.get("status", "").strip()
    diff_filter = request.args.get("difficulty", "").strip()
    os_filter = request.args.get("os", "").strip()
    cat_filter = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip().lower()

    query = """
        SELECT s.id, s.slug, s.name, s.status, s.current_version, s.created_at, s.updated_at,
               u.username as author_name,
               m.os_type, m.author_difficulty, m.reviewed_difficulty, m.category
        FROM machine_submissions s
        JOIN users u ON u.id = s.user_id
        LEFT JOIN machine_metadata m ON m.submission_id = s.id AND m.version_id = (
            SELECT id FROM machine_versions v WHERE v.submission_id = s.id ORDER BY v.id DESC LIMIT 1
        )
        WHERE 1=1
    """
    params = []

    if status_filter:
        query += " AND s.status = ?"
        params.append(status_filter)
    if diff_filter:
        query += " AND (m.author_difficulty = ? OR m.reviewed_difficulty = ?)"
        params.extend([diff_filter, diff_filter])
    if os_filter:
        query += " AND m.os_type = ?"
        params.append(os_filter)
    if cat_filter:
        query += " AND m.category = ?"
        params.append(cat_filter)
    if search:
        query += " AND (LOWER(s.name) LIKE ? OR LOWER(s.slug) LIKE ? OR LOWER(u.username) LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    query += " ORDER BY s.updated_at DESC"
    submissions = db.execute(query, params).fetchall()

    return render_template(
        "admin/machines_list.html",
        submissions=submissions,
        current_status=status_filter,
        current_diff=diff_filter,
        current_os=os_filter,
        current_cat=cat_filter,
        search=search,
        user=user
    )


@admin_bp.route("/admin/machines/<int:submission_id>")
@admin_required
def machine_review_workspace(submission_id):
    """Página de Análise Administrativa com as 10 Abas especializadas."""
    user = current_user()
    db = get_db()

    sub = db.execute(
        """SELECT s.*, u.username as author_name
           FROM machine_submissions s
           JOIN users u ON u.id = s.user_id
           WHERE s.id = ?""",
        (submission_id,)
    ).fetchone()

    if not sub:
        abort(404)

    # Versões
    versions = db.execute(
        "SELECT * FROM machine_versions WHERE submission_id = ? ORDER BY id DESC",
        (submission_id,)
    ).fetchall()

    latest_ver = versions[0] if versions else None
    ver_id = latest_ver["id"] if latest_ver else 0

    # Metadados da versão atual
    metadata = db.execute("SELECT * FROM machine_metadata WHERE version_id = ?", (ver_id,)).fetchone()

    # Parse de JSONs educacionais
    objectives = json.loads(metadata["objectives_json"]) if metadata and metadata["objectives_json"] else []
    prerequisites = json.loads(metadata["prerequisites_json"]) if metadata and metadata["prerequisites_json"] else []
    hints = json.loads(metadata["hints_json"]) if metadata and metadata["hints_json"] else []
    references = json.loads(metadata["references_json"]) if metadata and metadata["references_json"] else []
    exposed_ports = json.loads(metadata["exposed_ports_json"]) if metadata and metadata["exposed_ports_json"] else [80]

    # Arquivos
    files = db.execute("SELECT * FROM machine_files WHERE version_id = ? ORDER BY file_path ASC", (ver_id,)).fetchall()

    # Builds
    builds = db.execute("SELECT * FROM machine_builds WHERE version_id = ? ORDER BY id DESC", (ver_id,)).fetchall()
    latest_build = builds[0] if builds else None

    # Scans e Findings
    scans = db.execute("SELECT * FROM machine_scans WHERE version_id = ? ORDER BY id DESC", (ver_id,)).fetchall()
    findings = db.execute("SELECT * FROM machine_findings WHERE version_id = ? ORDER BY severity ASC, id DESC", (ver_id,)).fetchall()

    # Testes
    tests = db.execute("SELECT * FROM machine_tests WHERE version_id = ? ORDER BY id ASC", (ver_id,)).fetchall()

    # Flags
    flags = db.execute("SELECT * FROM machine_flags WHERE version_id = ? ORDER BY id ASC", (ver_id,)).fetchall()

    # Comentários
    comments = db.execute(
        """SELECT c.*, u.username
           FROM machine_review_comments c
           JOIN users u ON u.id = c.user_id
           WHERE c.submission_id = ?
           ORDER BY c.created_at ASC""",
        (submission_id,)
    ).fetchall()

    # Histórico de estados
    history = db.execute(
        """SELECT h.*, u.username as changed_by
           FROM machine_status_history h
           LEFT JOIN users u ON u.id = h.changed_by_user_id
           WHERE h.submission_id = ?
           ORDER BY h.created_at DESC""",
        (submission_id,)
    ).fetchall()

    # Revisões anteriores
    reviews = db.execute(
        """SELECT r.*, u.username as reviewer_name
           FROM machine_reviews r
           JOIN users u ON u.id = r.reviewer_id
           WHERE r.submission_id = ?
           ORDER BY r.id DESC""",
        (submission_id,)
    ).fetchall()

    # Scorecard de validação para publicação
    has_metadata = bool(metadata and metadata["short_desc"])
    has_build = bool(latest_build and latest_build["status"] == "success")
    has_security_pass = not any(f["severity"] == "CRITICAL" and not f["is_expected"] for f in findings)
    has_tests_pass = len(tests) > 0 and all(t["status"] == "passed" for t in tests)
    has_flags = len(flags) > 0
    has_learning = len(objectives) > 0

    scorecard = {
        "metadata": has_metadata,
        "build": has_build,
        "security": has_security_pass,
        "tests": has_tests_pass,
        "flags": has_flags,
        "learning": has_learning,
        "ready_to_publish": (has_metadata and has_build and has_security_pass and has_tests_pass and has_flags and has_learning)
    }

    return render_template(
        "admin/machine_review.html",
        sub=sub,
        latest_ver=latest_ver,
        metadata=metadata,
        objectives=objectives,
        prerequisites=prerequisites,
        hints=hints,
        references=references,
        exposed_ports=exposed_ports,
        files=files,
        builds=builds,
        latest_build=latest_build,
        scans=scans,
        findings=findings,
        tests=tests,
        flags=flags,
        comments=comments,
        history=history,
        reviews=reviews,
        scorecard=scorecard,
        user=user
    )


@admin_bp.route("/admin/machines/published")
@admin_required
def published_machines():
    """Gerenciamento de máquinas publicadas no catálogo ativo."""
    user = current_user()
    db = get_db()

    rows = db.execute(
        """SELECT p.id as pub_id, p.challenge_id, p.published_version, p.is_active, p.published_at, p.unpublished_at,
                  s.id as sub_id, s.name, s.slug, u.username as author_name,
                  m.os_type, m.author_difficulty, m.reviewed_difficulty, m.category
           FROM published_machines p
           JOIN machine_submissions s ON s.id = p.submission_id
           JOIN users u ON u.id = s.user_id
           LEFT JOIN machine_metadata m ON m.submission_id = s.id AND m.version_id = (
               SELECT id FROM machine_versions v WHERE v.submission_id = s.id ORDER BY v.id DESC LIMIT 1
           )
           ORDER BY p.published_at DESC"""
    ).fetchall()

    return render_template("admin/published_machines.html", machines=rows, user=user)


@admin_bp.route("/admin/audit")
@admin_required
def audit_logs():
    """Tela de auditoria completa da esteira de submissão e revisão de máquinas."""
    user = current_user()
    db = get_db()

    action_filter = request.args.get("action", "").strip()
    query = """
        SELECT a.*, u.username
        FROM machine_audit_logs a
        LEFT JOIN users u ON u.id = a.user_id
        WHERE 1=1
    """
    params = []
    if action_filter:
        query += " AND a.action LIKE ?"
        params.append(f"%{action_filter}%")

    query += " ORDER BY a.created_at DESC LIMIT 100"
    logs = db.execute(query, params).fetchall()

    return render_template("admin/audit.html", logs=logs, current_action=action_filter, user=user)


# ══════════════════════════════════════════════════════════════════════════════
# 2. ENDPOINTS DE API ADMINISTRATIVA (PIPELINE, DECISÕES E LEITURA DE ARQUIVO)
# ══════════════════════════════════════════════════════════════════════════════

@admin_bp.route("/api/admin/machines/<int:submission_id>/file", methods=["GET"])
@admin_required
def api_get_file_content(submission_id):
    """Retorna o conteúdo textual de um arquivo da máquina para exibição com syntax highlighting."""
    db = get_db()
    file_path = request.args.get("path", "").strip()
    if not file_path:
        return jsonify({"error": "Parâmetro 'path' é obrigatório"}), 400

    latest_ver = db.execute(
        "SELECT extracted_path FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if not latest_ver or not latest_ver["extracted_path"]:
        return jsonify({"error": "Diretório do pacote não encontrado"}), 404

    base = Path(latest_ver["extracted_path"]).resolve()
    target = (base / file_path).resolve()

    # Prevenção de Path Traversal
    if not str(target).startswith(str(base)):
        return jsonify({"error": "Acesso negado: fora do diretório do pacote"}), 403

    if not target.is_file():
        return jsonify({"error": "Arquivo não encontrado"}), 404

    # Não permite abrir arquivos gigantes
    if target.stat().st_size > 500 * 1024:
        return jsonify({"error": "Arquivo muito grande para visualização direta (limite: 500KB)"}), 400

    try:
        content = target.read_text(encoding="utf-8", errors="replace")
        return jsonify({"path": file_path, "content": content})
    except Exception as e:
        return jsonify({"error": f"Erro ao ler arquivo: {e}"}), 500


@admin_bp.route("/api/admin/machines/<int:submission_id>/build", methods=["POST"])
@admin_required
def api_trigger_build(submission_id):
    """Aciona o build isolado da versão atual da máquina."""
    user = current_user()
    db = get_db()

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if not latest_ver:
        return jsonify({"error": "Versão não encontrada"}), 404

    # Atualiza status para BUILDING
    try:
        transition_submission(db, submission_id, "BUILDING", user["id"], "Início de build isolado")
    except StateTransitionError:
        pass

    result = run_build_job(db, latest_ver["id"])
    return jsonify(result)


@admin_bp.route("/api/admin/machines/<int:submission_id>/scan", methods=["POST"])
@admin_required
def api_trigger_scan(submission_id):
    """Executa varredura estática de segurança e scanner de segredos."""
    user = current_user()
    db = get_db()

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if not latest_ver:
        return jsonify({"error": "Versão não encontrada"}), 404

    try:
        transition_submission(db, submission_id, "SECURITY_REVIEW", user["id"], "Início de varredura de segurança")
    except StateTransitionError:
        pass

    result = run_scan_job(db, latest_ver["id"])
    return jsonify(result)


@admin_bp.route("/api/admin/machines/<int:submission_id>/test", methods=["POST"])
@admin_required
def api_trigger_tests(submission_id):
    """Executa os testes funcionais de runtime e integridade no sandbox."""
    user = current_user()
    db = get_db()

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if not latest_ver:
        return jsonify({"error": "Versão não encontrada"}), 404

    try:
        transition_submission(db, submission_id, "FUNCTIONAL_TEST", user["id"], "Início de testes de sandbox")
    except StateTransitionError:
        pass

    result = run_test_job(db, latest_ver["id"])
    return jsonify(result)


@admin_bp.route("/api/admin/machines/<int:submission_id>/finding/<int:finding_id>", methods=["POST"])
@admin_required
def api_update_finding(submission_id, finding_id):
    """Permite ao revisor classificar um finding como 'Expected' (esperado) e adicionar nota."""
    user = current_user()
    db = get_db()

    data = request.get_json(silent=True) or {}
    is_expected = 1 if data.get("is_expected") in (True, 1, "1", "true") else 0
    admin_note = str(data.get("admin_note", "")).strip()

    db.execute(
        """UPDATE machine_findings 
           SET is_expected = ?, admin_note = ?, status = 'acknowledged'
           WHERE id = ? AND version_id IN (SELECT id FROM machine_versions WHERE submission_id = ?)""",
        (is_expected, admin_note, finding_id, submission_id)
    )
    db.commit()

    log_machine_audit(
        db, user["id"], "UPDATE_FINDING", "machine_findings", str(finding_id),
        "SUCCESS", request.remote_addr, {"is_expected": is_expected, "admin_note": admin_note}
    )

    return jsonify({"success": True, "finding_id": finding_id, "is_expected": is_expected})


@admin_bp.route("/api/admin/machines/<int:submission_id>/difficulty", methods=["POST"])
@admin_required
def api_update_difficulty(submission_id):
    """Permite ao revisor ajustar a dificuldade avaliada sem sobrescrever a do autor."""
    user = current_user()
    db = get_db()

    data = request.get_json(silent=True) or {}
    reviewed_diff = str(data.get("reviewed_difficulty") or data.get("difficulty") or "").strip()
    reason = str(data.get("difficulty_reason") or data.get("reason") or "").strip()

    if not reviewed_diff:
        return jsonify({"error": "Dificuldade avaliada é obrigatória"}), 400

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if latest_ver:
        db.execute(
            """UPDATE machine_metadata 
               SET reviewed_difficulty = ?, difficulty_reason = ? 
               WHERE version_id = ?""",
            (reviewed_diff, reason, latest_ver["id"])
        )
        db.commit()

    log_machine_audit(
        db, user["id"], "REVIEW_DIFFICULTY", "machine_metadata", str(submission_id),
        "SUCCESS", request.remote_addr, {"reviewed_difficulty": reviewed_diff, "reason": reason}
    )

    return jsonify({"success": True, "reviewed_difficulty": reviewed_diff, "difficulty_reason": reason})


@admin_bp.route("/api/admin/machines/<int:submission_id>/request-changes", methods=["POST"])
@admin_required
def api_request_changes(submission_id):
    """Revisor solicita alterações ao autor, com motivo obrigatório."""
    user = current_user()
    db = get_db()

    data = request.get_json(silent=True) or {}
    reason = str(data.get("reason", "")).strip()
    if not reason:
        return jsonify({"error": "O motivo da solicitação de alterações é obrigatório."}), 400

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    ver_id = latest_ver["id"] if latest_ver else None

    # Registra revisão
    db.execute(
        """INSERT INTO machine_reviews (submission_id, version_id, reviewer_id, decision, reason, category)
           VALUES (?, ?, ?, 'CHANGES_REQUESTED', ?, 'Reviewer Feedback')""",
        (submission_id, ver_id, user["id"], reason)
    )

    # Adiciona no chat de comunicação
    db.execute(
        """INSERT INTO machine_review_comments (submission_id, user_id, author_role, comment_text)
           VALUES (?, ?, 'reviewer', ?)""",
        (submission_id, user["id"], f"[SOLICITAÇÃO DE ALTERAÇÕES]: {reason}")
    )

    # Transiciona estado para CHANGES_REQUESTED
    try:
        transition_submission(db, submission_id, "CHANGES_REQUESTED", user["id"], reason, request.remote_addr)
    except StateTransitionError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"success": True, "status": "CHANGES_REQUESTED"})


@admin_bp.route("/api/admin/machines/<int:submission_id>/reject", methods=["POST"])
@admin_required
def api_reject_machine(submission_id):
    """Rejeita a submissão de máquina com categoria e motivo obrigatórios."""
    user = current_user()
    db = get_db()

    data = request.get_json(silent=True) or {}
    reason = str(data.get("reason", "")).strip()
    category = str(data.get("category", "Policy")).strip()

    if not reason:
        return jsonify({"error": "O motivo da rejeição é obrigatório."}), 400

    latest_ver = db.execute(
        "SELECT id FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()
    ver_id = latest_ver["id"] if latest_ver else None

    # Registra revisão de rejeição
    db.execute(
        """INSERT INTO machine_reviews (submission_id, version_id, reviewer_id, decision, reason, category)
           VALUES (?, ?, ?, 'REJECTED', ?, ?)""",
        (submission_id, ver_id, user["id"], reason, category)
    )

    # Adiciona comentário explicativo
    db.execute(
        """INSERT INTO machine_review_comments (submission_id, user_id, author_role, comment_text)
           VALUES (?, ?, 'reviewer', ?)""",
        (submission_id, user["id"], f"[SUBMISSÃO REJEITADA ({category})]: {reason}")
    )

    try:
        transition_submission(db, submission_id, "REJECTED", user["id"], f"Rejeitada: {reason}", request.remote_addr)
    except StateTransitionError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"success": True, "status": "REJECTED"})


@admin_bp.route("/api/admin/machines/<int:submission_id>/approve", methods=["POST"])
@admin_bp.route("/api/admin/machines/<int:submission_id>/approve-publish", methods=["POST"])
@admin_required
def api_approve_and_publish(submission_id):
    """Aprova e publica a máquina no catálogo oficial."""
    user = current_user()
    db = get_db()

    sub = db.execute("SELECT * FROM machine_submissions WHERE id = ?", (submission_id,)).fetchone()
    if not sub:
        return jsonify({"error": "Submissão não encontrada"}), 404

    latest_ver = db.execute(
        "SELECT id, version_str FROM machine_versions WHERE submission_id = ? ORDER BY id DESC LIMIT 1",
        (submission_id,)
    ).fetchone()

    if not latest_ver:
        return jsonify({"error": "Nenhuma versão encontrada"}), 400

    ver_id = latest_ver["id"]
    ver_str = latest_ver["version_str"]

    # Registra aprovação
    db.execute(
        """INSERT INTO machine_reviews (submission_id, version_id, reviewer_id, decision, reason, category)
           VALUES (?, ?, ?, 'APPROVED', 'Máquina validada em todos os gates técnicos e educacionais.', 'Publication')""",
        (submission_id, ver_id, user["id"])
    )

    # Publica na tabela published_machines
    challenge_id = f"machine-{sub['slug']}"
    db.execute(
        """INSERT INTO published_machines (submission_id, challenge_id, published_version, is_active)
           VALUES (?, ?, ?, 1)
           ON CONFLICT(submission_id) DO UPDATE SET 
               published_version = excluded.published_version,
               is_active = 1,
               published_at = CURRENT_TIMESTAMP,
               unpublished_at = NULL""",
        (submission_id, challenge_id, ver_str)
    )

    # Transiciona estado para PUBLISHED
    try:
        transition_submission(db, submission_id, "PUBLISHED", user["id"], "Aprovada e publicada no catálogo oficial", request.remote_addr)
    except StateTransitionError as e:
        return jsonify({"error": str(e)}), 400

    log_machine_audit(
        db, user["id"], "APPROVE_AND_PUBLISH", "published_machines", str(submission_id),
        "SUCCESS", request.remote_addr, {"challenge_id": challenge_id, "version": ver_str}
    )

    return jsonify({
        "success": True,
        "status": "PUBLISHED",
        "challenge_id": challenge_id,
        "version": ver_str
    })


@admin_bp.route("/api/admin/machines/<int:submission_id>/unpublish", methods=["POST"])
@admin_required
def api_unpublish_machine(submission_id):
    """Despublica uma máquina ativa do catálogo."""
    user = current_user()
    db = get_db()

    db.execute(
        """UPDATE published_machines 
           SET is_active = 0, unpublished_at = CURRENT_TIMESTAMP 
           WHERE submission_id = ?""",
        (submission_id,)
    )

    try:
        transition_submission(db, submission_id, "UNPUBLISHED", user["id"], "Máquina despublicada pelo administrador", request.remote_addr)
    except StateTransitionError as e:
        return jsonify({"error": str(e)}), 400

    log_machine_audit(
        db, user["id"], "UNPUBLISH_MACHINE", "published_machines", str(submission_id),
        "SUCCESS", request.remote_addr, {"submission_id": submission_id}
    )

    return jsonify({"success": True, "status": "UNPUBLISHED"})
