"""modules/kids/routes.py — Rotas da DUNO Kids (Dashboard, Skill Tree, Quiz, Quests, Leaderboard)."""
import json
from datetime import datetime, date
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort, g
from core.auth import current_user
from core.decorators import login_required
from core.database import get_db
from modules.kids.kids_db import init_kids_db, get_or_create_kids_stats
from modules.kids.kids_content import get_lesson_interactive_data

bp = Blueprint("kids", __name__, url_prefix="/kids")


@bp.before_request
def setup_kids_context():
    """Garante que as tabelas Kids estejam prontas antes de qualquer requisição."""
    db = get_db()
    init_kids_db(db)


@bp.route("/")
@bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard principal da DUNO Kids com Skill Tree e painel gamificado."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    # Carrega módulos disponíveis
    modules = db.execute("SELECT * FROM kids_modules ORDER BY order_idx ASC").fetchall()
    active_module_id = request.args.get("module", "networks")

    # Garante que active_module_id seja válido
    valid_module_ids = [m["id"] for m in modules]
    if active_module_id not in valid_module_ids and valid_module_ids:
        active_module_id = valid_module_ids[0]

    current_module = db.execute("SELECT * FROM kids_modules WHERE id = ?", (active_module_id,)).fetchone()

    # Carrega lições do módulo selecionado
    lessons_rows = db.execute(
        "SELECT * FROM kids_lessons WHERE module_id = ? ORDER BY order_idx ASC",
        (active_module_id,)
    ).fetchall()

    # Carrega o progresso do usuário para essas lições
    user_progress = {
        row["lesson_id"]: row for row in db.execute(
            "SELECT * FROM kids_progress WHERE user_id = ?",
            (user["id"],)
        ).fetchall()
    }

    # Monta a árvore de lições com estados desbloqueados/bloqueados
    skill_tree = []
    prev_completed = True  # A primeira lição sempre inicia disponível
    for l in lessons_rows:
        lid = l["id"]
        prog = user_progress.get(lid)
        
        if prog and prog["status"] == "completed":
            status = "completed"
            stars = prog["stars"]
            prev_completed = True
        elif prev_completed:
            status = "available"
            stars = 0
            prev_completed = False
        else:
            status = "locked"
            stars = 0

        skill_tree.append({
            "id": l["id"],
            "slug": l["slug"],
            "title": l["title"],
            "subtitle": l["subtitle"],
            "icon": l["icon"],
            "order_idx": l["order_idx"],
            "xp_reward": l["xp_reward"],
            "coins_reward": l["coins_reward"],
            "status": status,
            "stars": stars
        })

    # Carrega missões diárias ativas do usuário
    today_str = date.today().isoformat()
    quests = db.execute(
        "SELECT * FROM kids_quests WHERE user_id = ? AND quest_date = ? ORDER BY id ASC",
        (user["id"], today_str)
    ).fetchall()

    # Calcula percentual de progresso do módulo
    completed_count = sum(1 for item in skill_tree if item["status"] == "completed")
    total_count = len(skill_tree)
    progress_pct = int((completed_count / total_count * 100)) if total_count > 0 else 0
    is_module_completed = (completed_count == total_count and total_count > 0)

    # Mapeamento do Funil para a DUNO Academy (docs/leia.md)
    academy_targets = {
        "os": {"url": url_for("command_injection.index"), "name": "Lab 02: Command Injection", "desc": "Pratique execução de comandos no Linux real!"},
        "networks": {"url": url_for("csrf.index"), "name": "Lab 03: CSRF & Requisições Web", "desc": "Teste requisições HTTP reais e tokens de segurança!"},
        "programming": {"url": url_for("sqli.index"), "name": "Lab 07: SQL Injection", "desc": "Explore lógica e consultas de banco de dados!"},
        "security": {"url": url_for("brute_force.index"), "name": "Lab 01: Brute Force", "desc": "Quebre senhas fracas e domine autenticação!"},
        "english": {"url": url_for("documentation"), "name": "Documentação Oficial", "desc": "Consulte manuais e referências técnicas em inglês!"}
    }
    academy_funnel = academy_targets.get(active_module_id, {"url": url_for("academy_hub"), "name": "DUNO Academy", "desc": "Laboratórios práticos"})

    return render_template(
        "kids/dashboard.html",
        user=user,
        stats=stats,
        modules=modules,
        current_module=current_module,
        active_module_id=active_module_id,
        skill_tree=skill_tree,
        quests=quests,
        progress_pct=progress_pct,
        completed_count=completed_count,
        total_count=total_count,
        is_module_completed=is_module_completed,
        academy_funnel=academy_funnel,
        active_kids_tab="dashboard"
    )


@bp.route("/quiz/<int:lesson_id>")
@login_required
def quiz_view(lesson_id):
    """Arena de Aprendizado Interativo guiado pelo Tux (Teoria + Lab + Checkpoint)."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    lesson = db.execute("SELECT * FROM kids_lessons WHERE id = ?", (lesson_id,)).fetchone()
    if not lesson:
        abort(404)

    # Carrega perguntas do quiz
    quizzes = db.execute(
        "SELECT id, order_idx, question, option_a, option_b, option_c, option_d, xp FROM kids_quizzes WHERE lesson_id = ? ORDER BY order_idx ASC",
        (lesson_id,)
    ).fetchall()

    if not quizzes:
        return redirect(url_for("kids.dashboard"))

    # Carrega dados pedagógicos interativos (slides de história/teoria, laboratório e dicas)
    interactive_data = get_lesson_interactive_data(lesson_id)

    return render_template(
        "kids/quiz.html",
        user=user,
        stats=stats,
        lesson=lesson,
        quizzes=quizzes,
        total_questions=len(quizzes),
        interactive_data=interactive_data
    )


@bp.route("/quests")
@login_required
def quests_view():
    """Tela dedicada de Missões Diárias e Baús de Recompensa."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])
    today_str = date.today().isoformat()

    quests = db.execute(
        "SELECT * FROM kids_quests WHERE user_id = ? AND quest_date = ? ORDER BY id ASC",
        (user["id"], today_str)
    ).fetchall()

    return render_template(
        "kids/quests.html",
        user=user,
        stats=stats,
        quests=quests,
        active_kids_tab="quests"
    )


@bp.route("/leaderboard")
@login_required
def leaderboard_view():
    """Ranking de alunos por Ligas (Bronze, Prata, Ouro, Diamante)."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    # Ranking ordenado por XP com junção com tabela de usuários
    ranking = db.execute(
        """SELECT u.id, u.username, s.xp, s.level, s.league, s.streak_days
           FROM kids_user_stats s
           JOIN users u ON u.id = s.user_id
           ORDER BY s.xp DESC LIMIT 20"""
    ).fetchall()

    return render_template(
        "kids/leaderboard.html",
        user=user,
        stats=stats,
        ranking=ranking,
        active_kids_tab="leaderboard"
    )


# ════════════════════════════════════════════════════════════════════════════════
# APIS REST / JSON (Validadas estritamente no backend — Regra de Segurança §17)
# ════════════════════════════════════════════════════════════════════════════════

@bp.route("/api/quiz/answer", methods=["POST"])
@login_required
def answer_quiz():
    """Valida a resposta do quiz no servidor, desconta vida em caso de erro e calcula XP."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    data = request.get_json(silent=True) or {}
    quiz_id = data.get("quiz_id")
    answer = str(data.get("answer", "")).strip().upper()

    if not quiz_id or answer not in ("A", "B", "C", "D"):
        return jsonify({"error": "Dados de resposta inválidos"}), 400

    quiz = db.execute("SELECT * FROM kids_quizzes WHERE id = ?", (quiz_id,)).fetchone()
    if not quiz:
        return jsonify({"error": "Quiz não encontrado"}), 404

    is_correct = (answer == quiz["correct_option"].upper())
    xp_gained = quiz["xp"] if is_correct else 0
    lives = stats["lives"]

    interactive_data = get_lesson_interactive_data(quiz["lesson_id"])
    tux_hint = interactive_data.get("hint", "")

    if is_correct:
        # Incrementa XP do usuário
        new_xp = stats["xp"] + xp_gained
        new_level = (new_xp // 500) + 1
        db.execute(
            "UPDATE kids_user_stats SET xp = ?, level = ? WHERE user_id = ?",
            (new_xp, new_level, user["id"])
        )
        # Atualiza missão de acertar perguntas
        today_str = date.today().isoformat()
        db.execute(
            """UPDATE kids_quests 
               SET current_count = MIN(target_count, current_count + 1)
               WHERE user_id = ? AND quest_date = ? AND title LIKE '%Acertar%'""",
            (user["id"], today_str)
        )
        tux_reaction = "Brilhante! Você acertou em cheio! O Tux está comemorando com você!"
        mascot_pose = "animado"
    else:
        # Resposta incorreta: perde 1 vida
        lives = max(0, lives - 1)
        db.execute("UPDATE kids_user_stats SET lives = ? WHERE user_id = ?", (lives, user["id"]))
        tux_reaction = f"Quase lá! {tux_hint}"
        mascot_pose = "guiando"

    db.commit()

    return jsonify({
        "correct": is_correct,
        "correct_option": quiz["correct_option"],
        "explanation": quiz["explanation"],
        "xp_gained": xp_gained,
        "lives_remaining": lives,
        "game_over": (lives == 0),
        "tux_reaction": tux_reaction,
        "tux_hint": tux_hint,
        "mascot_pose": mascot_pose
    })


@bp.route("/api/lab/execute", methods=["POST"])
@login_required
def execute_lab():
    """Valida a execução prática no Mini-Lab interativo (Terminal, Sequência, Inspetor)."""
    user = current_user()
    if not user:
        abort(401)

    data = request.get_json(silent=True) or {}
    lesson_id = int(data.get("lesson_id", 0))
    action_type = data.get("type", "terminal")
    command = str(data.get("command", "")).strip()

    interactive_data = get_lesson_interactive_data(lesson_id)
    lab = interactive_data.get("lab", {})

    if action_type == "terminal":
        commands_map = lab.get("commands", {})
        if command in ("clear", "cls"):
            return jsonify({
                "output": "",
                "clear": True,
                "tux_reaction": "Tela limpa! Continue explorando.",
                "completed": False,
                "mascot_pose": "guiando"
            })
        elif command in ("help", "?"):
            accepted = ", ".join(commands_map.keys())
            return jsonify({
                "output": f"Comandos disponíveis neste lab: {accepted}",
                "tux_reaction": "Experimente um dos comandos sugeridos nas instruções!",
                "completed": False,
                "mascot_pose": "guiando"
            })

        # Checa comando exato
        cmd_entry = commands_map.get(command)
        if cmd_entry:
            return jsonify({
                "output": cmd_entry.get("output", ""),
                "tux_reaction": cmd_entry.get("tux_reaction", "Muito bem!"),
                "completed": cmd_entry.get("completed", False),
                "mascot_pose": "animado" if cmd_entry.get("completed", False) else "guiando"
            })
        else:
            target = lab.get("target_command", "")
            return jsonify({
                "output": f"bash: {command}: comando desconhecido neste laboratório.\nDica do Tux: experimente digitar '{target}' ou use os atalhos rápidos abaixo.",
                "tux_reaction": f"Não se preocupe! Tente executar: {target}",
                "completed": False,
                "mascot_pose": "guiando"
            })

    elif action_type == "sequence":
        user_sequence = data.get("sequence", [])
        target_sequence = lab.get("target_sequence", [])
        is_correct = (user_sequence == target_sequence)
        return jsonify({
            "correct": is_correct,
            "tux_reaction": lab.get("tux_reaction", "Ordem perfeita!") if is_correct else "Ops! A sequência lógica ainda não está certa. Lembre-se da ordem de execução!",
            "completed": is_correct,
            "mascot_pose": "animado" if is_correct else "guiando"
        })

    elif action_type == "inspector":
        selected_answer = str(data.get("answer", "")).strip()
        target_answer = str(lab.get("target_answer", "")).strip()
        is_correct = (selected_answer == target_answer)
        return jsonify({
            "correct": is_correct,
            "tux_reaction": lab.get("tux_reaction", "Na mosca!") if is_correct else "Atenção: esse item é legítimo. Olhe os detalhes com cautela!",
            "completed": is_correct,
            "mascot_pose": "animado" if is_correct else "guiando"
        })

    return jsonify({"error": "Tipo de laboratório inválido"}), 400


@bp.route("/api/lesson/complete", methods=["POST"])
@login_required
def complete_lesson():
    """Conclui uma lição, grava estrelas, concede moedas e desbloqueia a próxima lição."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    data = request.get_json(silent=True) or {}
    lesson_id = data.get("lesson_id")
    correct_count = int(data.get("correct_count", 0))
    total_count = int(data.get("total_count", 1))

    lesson = db.execute("SELECT * FROM kids_lessons WHERE id = ?", (lesson_id,)).fetchone()
    if not lesson:
        return jsonify({"error": "Lição não encontrada"}), 404

    # Calcula estrelas (3 estrelas se 100%, 2 estrelas se >= 66%, 1 estrela caso contrário)
    ratio = (correct_count / total_count) if total_count > 0 else 0
    if ratio >= 0.99:
        stars = 3
    elif ratio >= 0.66:
        stars = 2
    else:
        stars = 1

    # Registra progresso
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    db.execute(
        """INSERT INTO kids_progress (user_id, lesson_id, status, stars, score, completed_at)
           VALUES (?, ?, 'completed', ?, ?, ?)
           ON CONFLICT(user_id, lesson_id) DO UPDATE SET
             status = 'completed',
             stars = MAX(stars, excluded.stars),
             completed_at = excluded.completed_at""",
        (user["id"], lesson_id, stars, correct_count, now_str)
    )

    # Concede recompensas da lição
    new_coins = stats["coins"] + lesson["coins_reward"]
    new_xp = stats["xp"] + lesson["xp_reward"]
    new_level = (new_xp // 500) + 1
    db.execute(
        "UPDATE kids_user_stats SET coins = ?, xp = ?, level = ? WHERE user_id = ?",
        (new_coins, new_xp, new_level, user["id"])
    )

    # Atualiza missão diária de completar lição
    today_str = date.today().isoformat()
    db.execute(
        """UPDATE kids_quests 
           SET current_count = MIN(target_count, current_count + 1)
           WHERE user_id = ? AND quest_date = ? AND title LIKE '%Lição%'""",
        (user["id"], today_str)
    )

    db.commit()

    return jsonify({
        "success": True,
        "stars": stars,
        "xp_reward": lesson["xp_reward"],
        "coins_reward": lesson["coins_reward"],
        "total_xp": new_xp,
        "total_coins": new_coins,
        "level": new_level
    })


@bp.route("/api/quest/claim", methods=["POST"])
@login_required
def claim_quest():
    """Resgata a recompensa de uma missão diária concluída."""
    user = current_user()
    if not user:
        abort(401)
    db = get_db()
    stats = get_or_create_kids_stats(db, user["id"])

    data = request.get_json(silent=True) or {}
    quest_id = data.get("quest_id")

    quest = db.execute("SELECT * FROM kids_quests WHERE id = ? AND user_id = ?", (quest_id, user["id"])).fetchone()
    if not quest:
        return jsonify({"error": "Missão não encontrada"}), 404

    if quest["claimed"]:
        return jsonify({"error": "Recompensa já resgatada"}), 400

    if quest["current_count"] < quest["target_count"]:
        return jsonify({"error": "Missão ainda não concluída"}), 400

    # Credita XP e moedas
    new_xp = stats["xp"] + quest["reward_xp"]
    new_coins = stats["coins"] + quest["reward_coins"]
    new_chests = stats["chests_opened"] + (1 if quest["reward_chest"] else 0)

    db.execute(
        "UPDATE kids_user_stats SET xp = ?, coins = ?, chests_opened = ? WHERE user_id = ?",
        (new_xp, new_coins, new_chests, user["id"])
    )
    db.execute("UPDATE kids_quests SET claimed = 1 WHERE id = ?", (quest_id,))
    db.commit()

    return jsonify({
        "success": True,
        "reward_xp": quest["reward_xp"],
        "reward_coins": quest["reward_coins"],
        "reward_chest": quest["reward_chest"],
        "total_xp": new_xp,
        "total_coins": new_coins
    })
