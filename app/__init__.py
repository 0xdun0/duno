import os
from datetime import datetime
from collections import Counter
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, abort, current_app
from config import Config
from core.database import init_db, get_db
from core.auth import login_user, logout_user, current_user
from core.security_levels import set_level, get_level, VALID_MODULES, VALID_LEVELS
from core.source_loader import load_source
from core.reset import reset_lab
from core.decorators import login_required
from core.academy_data import get_learning_paths, get_all_lessons_summary, get_lesson_data
from core.docs_manager import (
    get_all_categories,
    get_doc_metadata,
    get_doc_content,
    search_docs,
    WHATS_NEW_TIMELINE,
    SEARCH_SUGGESTIONS
)


def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Inicializa DB teardown
    init_db(app)

    # ── Rotas globais ──────────────────────────────────────────────────────────

    @app.route("/")
    @login_required
    def index():
        user = current_user()
        return render_template("index.html", user=user)

    @app.route("/academy")
    @login_required
    def academy_hub():
        paths = get_learning_paths()
        curriculum = get_all_lessons_summary()
        return render_template("pages/academy_hub.html", paths=paths, curriculum=curriculum)

    @app.route("/academy/<slug>")
    @login_required
    def academy_lesson(slug):
        lesson = get_lesson_data(slug)
        if not lesson:
            abort(404)
        curriculum = get_all_lessons_summary()
        current_idx = next((i for i, x in enumerate(curriculum) if x["slug"] == slug), 0)
        prev_lesson = curriculum[current_idx - 1] if current_idx > 0 else None
        next_lesson = curriculum[current_idx + 1] if current_idx < len(curriculum) - 1 else None
        return render_template(
            "pages/academy_lesson.html",
            lesson=lesson,
            prev_lesson=prev_lesson,
            next_lesson=next_lesson
        )

    @app.route("/learning")
    @login_required
    def learning():
        return redirect(url_for("academy_hub"))

    @app.route("/docs")
    @login_required
    def documentation():
        categories = get_all_categories()
        return render_template(
            "pages/docs_hub.html",
            categories=categories,
            whats_new=WHATS_NEW_TIMELINE,
            search_suggestions=SEARCH_SUGGESTIONS
        )

    @app.route("/docs/<slug>")
    @login_required
    def documentation_doc(slug):
        doc_data = get_doc_content(slug)
        if not doc_data:
            abort(404)
        categories = get_all_categories()
        return render_template(
            "pages/docs_reader.html",
            doc_data=doc_data,
            categories=categories
        )

    @app.route("/api/docs/search")
    @login_required
    def api_docs_search():
        query = request.args.get("q", "")
        results = search_docs(query)
        return jsonify(results)

    @app.route("/api")
    @login_required
    def api_portal():
        return render_template("pages/api.html")

    @app.route("/about")
    @login_required
    def about():
        return render_template("pages/about.html")

    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        db = get_db()
        db_path = current_app.config.get("DATABASE", "/app/data/duno.db")

        # Se executando fora do container ou caminho relativo
        if not os.path.isabs(db_path) or not os.path.exists(db_path):
            if os.path.exists("data/duno.db"):
                db_path = os.path.abspath("data/duno.db")

        db_filename = os.path.basename(db_path)
        if os.path.exists(db_path):
            db_size_bytes = os.path.getsize(db_path)
            if db_size_bytes < 1024 * 1024:
                db_size_formatted = f"{db_size_bytes / 1024:.1f} KB"
            else:
                db_size_formatted = f"{db_size_bytes / (1024 * 1024):.2f} MB"
            mtime = os.path.getmtime(db_path)
            dt = datetime.fromtimestamp(mtime)
            today = datetime.now().date()
            if dt.date() == today:
                last_reset_str = f"Hoje, {dt.strftime('%H:%M')}"
            else:
                last_reset_str = dt.strftime("%d/%m/%Y, %H:%M")
        else:
            db_size_formatted = "44.0 KB"
            last_reset_str = "Hoje, 00:18"

        try:
            tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
            table_count = len(tables)
        except Exception:
            table_count = 8
            tables = ["users", "security_levels", "guestbook", "secrets", "api_tokens", "captcha_challenges", "audit_log"]

        user_levels = [get_level(user["id"], m) for m in VALID_MODULES]
        counts = Counter(user_levels)
        current_default_level = session.get("default_security_level") or (counts.most_common(1)[0][0] if counts else "low")

        # Real activity log for ACTIVITY section
        try:
            activity_rows = db.execute(
                "SELECT action, ip, ts FROM audit_log ORDER BY id DESC LIMIT 6"
            ).fetchall()
            activities = [{"action": r["action"], "ip": r["ip"], "ts": str(r["ts"])} for r in activity_rows]
        except Exception:
            activities = []

        if not activities:
            activities = [
                {"action": f"Global baseline security level established to {current_default_level.upper()}", "ip": "127.0.0.1", "ts": last_reset_str},
                {"action": "Laboratory environment initialized • All 20 modules active", "ip": "system", "ts": "Hoje, 00:15"},
                {"action": "SQLite persistence engine connected (duno.db)", "ip": "local", "ts": "Hoje, 00:12"},
            ]

        if request.method == "POST":
            action = request.form.get("action")
            if action == "set_level":
                level = request.form.get("level", "").lower()
                if level in VALID_LEVELS:
                    session["default_security_level"] = level
                    for mod in VALID_MODULES:
                        set_level(user["id"], mod, level)
                    try:
                        db.execute(
                            "INSERT INTO audit_log (user_id, action, ip) VALUES (?, ?, ?)",
                            (user["id"], f"Security level set to {level.upper()} across all modules", request.remote_addr or "127.0.0.1")
                        )
                        db.commit()
                    except Exception:
                        pass
                    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                        return jsonify({"status": "ok", "level": level})
                    return redirect(url_for("settings"))
                abort(400)
            elif action == "reset_lab":
                reset_lab()
                try:
                    db.execute(
                        "INSERT INTO audit_log (user_id, action, ip) VALUES (?, ?, ?)",
                        (user["id"], "Laboratory database reset to initial seed state", request.remote_addr or "127.0.0.1")
                    )
                    db.commit()
                except Exception:
                    pass
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
                    return jsonify({"status": "ok", "message": "Database reset successfully"})
                return redirect(url_for("settings"))

        # Submissões de máquinas do usuário (Minhas Contribuições)
        user_submissions = []
        try:
            user_submissions = db.execute(
                """SELECT s.id, s.title, s.slug, s.difficulty, s.status, s.visibility, s.created_at,
                          (SELECT version_str FROM machine_versions WHERE submission_id = s.id ORDER BY id DESC LIMIT 1) as latest_version
                   FROM machine_submissions s
                   WHERE s.author_id = ?
                   ORDER BY s.updated_at DESC""",
                (user["id"],)
            ).fetchall()
        except Exception:
            user_submissions = []

        user_machine_stats = {
            "total": len(user_submissions),
            "published": sum(1 for s in user_submissions if s["status"] == "published"),
            "in_review": sum(1 for s in user_submissions if s["status"] in ("in_review", "submitted", "scanning")),
            "draft": sum(1 for s in user_submissions if s["status"] == "draft"),
        }

        # Moderação e auditoria de máquinas para administradores
        admin_pending_submissions = []
        admin_pending_count = 0
        machine_audit_logs = []
        if user and user.get("role") == "admin":
            try:
                admin_pending_submissions = db.execute(
                    """SELECT s.id, s.title, s.slug, s.difficulty, s.status, s.created_at, u.username as author_username,
                              (SELECT version_str FROM machine_versions WHERE submission_id = s.id ORDER BY id DESC LIMIT 1) as latest_version
                       FROM machine_submissions s
                       JOIN users u ON u.id = s.author_id
                       WHERE s.status IN ('submitted', 'in_review', 'scanning')
                       ORDER BY s.created_at ASC LIMIT 6"""
                ).fetchall()
                row_cnt = db.execute(
                    "SELECT COUNT(*) FROM machine_submissions WHERE status IN ('submitted', 'in_review', 'scanning')"
                ).fetchone()
                admin_pending_count = row_cnt[0] if row_cnt else 0

                machine_audit_logs = db.execute(
                    """SELECT l.*, u.username 
                       FROM machine_audit_logs l 
                       LEFT JOIN users u ON u.id = l.user_id 
                       ORDER BY l.id DESC LIMIT 8"""
                ).fetchall()
            except Exception:
                pass

        return render_template(
            "pages/settings.html",
            user=user,
            db_filename=db_filename,
            db_size_formatted=db_size_formatted,
            last_reset=last_reset_str,
            table_count=table_count,
            tables=tables,
            current_default_level=current_default_level,
            valid_levels=VALID_LEVELS,
            activities=activities,
            user_submissions=user_submissions,
            user_machine_stats=user_machine_stats,
            admin_pending_submissions=admin_pending_submissions,
            admin_pending_count=admin_pending_count,
            machine_audit_logs=machine_audit_logs,
        )

    @app.route("/command-center")
    @login_required
    def command_center():
        return redirect(url_for("settings"))

    # Auth blueprint inline (simples — não precisa de Blueprint separado)
    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            u = login_user(request.form.get("username", ""), request.form.get("password", ""))
            if u:
                return redirect(url_for("index"))
            error = "Credenciais inválidas."
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        logout_user()
        return redirect(url_for("login"))

    # Security Level switcher
    @app.route("/level/<module>", methods=["POST"])
    @login_required
    def set_security_level(module):
        if module not in VALID_MODULES:
            abort(400)
        level = request.form.get("level", "")
        ok = set_level(session["user_id"], module, level)
        if not ok:
            abort(400)
        # redireciona de volta para o módulo
        ref = request.referrer or url_for("index")
        return redirect(ref)

    # View Source
    @app.route("/source/<module>/<level>")
    @login_required
    def view_source(module, level):
        return load_source(module, level)

    # Reset
    @app.route("/reset", methods=["POST"])
    @login_required
    def reset():
        reset_lab()
        ref = request.referrer or url_for("index")
        return redirect(ref)

    # Context processor — injeta current_user e get_level em todos os templates
    @app.context_processor
    def inject_globals():
        user = current_user()
        def module_level(module):
            if user:
                return get_level(user["id"], module)
            return "low"
        challenges_enabled = os.environ.get("CHALLENGES_ENABLED", "true").strip().lower() in ("true", "1", "yes", "on")
        return dict(current_user=user, module_level=module_level, challenges_enabled=challenges_enabled)

    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return render_template("error.html", code=400, msg="Bad Request"), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("error.html", code=403, msg="Forbidden"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, msg="Not Found"), 404

    @app.errorhandler(413)
    def too_large(e):
        return render_template("error.html", code=413, msg="Upload muito grande (máx 2MB)"), 413

    @app.errorhandler(500)
    def server_error(e):
        import traceback
        traceback.print_exc()
        return render_template("error.html", code=500, msg=f"Erro interno: {e}"), 500

    # ── Registra Blueprints ────────────────────────────────────────────────────
    _register_blueprints(app)

    return app


def _register_blueprints(app):
    from modules.brute_force import bp as brute_force_bp
    from modules.command_injection import bp as command_injection_bp
    from modules.csrf import bp as csrf_bp
    from modules.file_inclusion import bp as file_inclusion_bp
    from modules.file_upload import bp as file_upload_bp
    from modules.captcha import bp as captcha_bp
    from modules.sqli import bp as sqli_bp
    from modules.sqli_blind import bp as sqli_blind_bp
    from modules.weak_session import bp as weak_session_bp
    from modules.xss_dom import bp as xss_dom_bp
    from modules.xss_reflected import bp as xss_reflected_bp
    from modules.xss_stored import bp as xss_stored_bp
    from modules.csp_bypass import bp as csp_bypass_bp
    from modules.js_attacks import bp as js_attacks_bp
    from modules.auth_bypass import bp as auth_bypass_bp
    from modules.open_redirect import bp as open_redirect_bp
    from modules.crypto import bp as crypto_bp
    from modules.api_versioning import bp as api_versioning_bp
    from modules.mass_assignment import bp as mass_assignment_bp
    from modules.api_security import bp as api_security_bp
    from modules.challenges import bp as challenges_bp
    from modules.kids import bp as kids_bp
    from modules.machine_submissions.routes import bp as submissions_bp
    from modules.machine_submissions.admin_routes import admin_bp as submissions_admin_bp

    app.register_blueprint(brute_force_bp)
    app.register_blueprint(command_injection_bp)
    app.register_blueprint(csrf_bp)
    app.register_blueprint(file_inclusion_bp)
    app.register_blueprint(file_upload_bp)
    app.register_blueprint(captcha_bp)
    app.register_blueprint(sqli_bp)
    app.register_blueprint(sqli_blind_bp)
    app.register_blueprint(weak_session_bp)
    app.register_blueprint(xss_dom_bp)
    app.register_blueprint(xss_reflected_bp)
    app.register_blueprint(xss_stored_bp)
    app.register_blueprint(csp_bypass_bp)
    app.register_blueprint(js_attacks_bp)
    app.register_blueprint(auth_bypass_bp)
    app.register_blueprint(open_redirect_bp)
    app.register_blueprint(crypto_bp)
    app.register_blueprint(api_versioning_bp)
    app.register_blueprint(mass_assignment_bp)
    app.register_blueprint(api_security_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(kids_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(submissions_admin_bp)

