"""core/auth.py — T-012 autenticação via sessão Flask."""
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
from core.database import get_db


def login_user(username: str, password: str):
    """
    Valida credenciais. Retorna dict do usuário ou None.
    Versão low: sem rate limit, sem brute-force protection.
    """
    db = get_db()
    user = db.execute(
        "SELECT * FROM users WHERE username=?", (username,)
    ).fetchone()
    if user and check_password_hash(user["password_hash"], password):
        session.clear()
        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["role"] = user["role"]
        return dict(user)
    return None


def logout_user():
    session.clear()


def current_user():
    """Retorna dict do usuário logado ou None."""
    uid = session.get("user_id")
    if uid is None:
        return None
    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def register_user(
    username: str,
    password: str,
    email: str = "",
    display_name: str = "",
    avatar: str = "robot",
    country: str = "BR",
    experience_level: str = "iniciante",
    interests: str | list[str] = "[]",
    profile_public: int = 1
):
    """
    Registra um novo usuário no banco, inicializando:
    - users (registro base)
    - user_stats (gamificação / XP / solves)
    - user_preferences (tema, compact_mode, animações)
    - user_privacy (visibilidade de perfil e ranking)
    - security_levels (nível 'low' para todos os 20 módulos)
    Retorna o dict do usuário criado ou lança ValueError em caso de validação.
    """
    import json
    import re
    from core.security_levels import VALID_MODULES, set_level

    clean_username = username.strip().lower()
    if not clean_username:
        raise ValueError("O nome de usuário não pode ser vazio.")
    if len(clean_username) < 3 or len(clean_username) > 25:
        raise ValueError("O nome de usuário deve ter entre 3 e 25 caracteres.")
    if not re.match(r"^[a-z0-9_\-]+$", clean_username):
        raise ValueError("O nome de usuário deve conter apenas letras minúsculas, números, '_' ou '-'.")
    if len(password) < 6:
        raise ValueError("A senha deve possuir no mínimo 6 caracteres.")

    db = get_db()

    # Verifica se já existe username
    exists = db.execute("SELECT id FROM users WHERE LOWER(username) = ?", (clean_username,)).fetchone()
    if exists:
        raise ValueError(f"O nome de usuário '{clean_username}' já está em uso.")

    # Inserção na tabela users
    p_hash = generate_password_hash(password)
    cur = db.execute(
        """INSERT INTO users (
               username, email, password_hash, display_name, avatar, 
               bio, country, experience_level, interests, role
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'user')""",
        (
            clean_username,
            email.strip() if email else None,
            p_hash,
            display_name.strip() if display_name else clean_username,
            avatar or "robot",
            "",
            country or "BR",
            experience_level or "iniciante",
            interests if isinstance(interests, str) else json.dumps(interests or [])
        )
    )
    user_id = cur.lastrowid

    # Inicializa user_stats
    db.execute(
        "INSERT OR IGNORE INTO user_stats (user_id, xp, level) VALUES (?, 0, 1)",
        (user_id,)
    )

    # Inicializa user_preferences
    db.execute(
        "INSERT OR IGNORE INTO user_preferences (user_id, theme, accent_color) VALUES (?, 'dark', 'orange')",
        (user_id,)
    )

    # Inicializa user_privacy
    db.execute(
        "INSERT OR IGNORE INTO user_privacy (user_id, profile_public) VALUES (?, ?)",
        (user_id, 1 if profile_public else 0)
    )

    # Inicializa todos os 20 módulos com nível 'low'
    for mod in VALID_MODULES:
        db.execute(
            "INSERT OR IGNORE INTO security_levels (user_id, module, level) VALUES (?, ?, 'low')",
            (user_id, mod)
        )

    db.commit()

    # Retorna o usuário criado
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)
