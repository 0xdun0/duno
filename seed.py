"""seed.py — T-010 criação e seed inicial do banco DUNO."""
import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get("DATABASE", "/app/data/duno.db")

DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    avatar TEXT DEFAULT 'robot',
    bio TEXT,
    country TEXT DEFAULT 'BR',
    experience_level TEXT DEFAULT 'iniciante',
    interests TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    challenges_solved INTEGER DEFAULT 0,
    machines_solved INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY,
    theme TEXT DEFAULT 'dark',
    accent_color TEXT DEFAULT 'orange',
    compact_mode INTEGER DEFAULT 0,
    animations_enabled INTEGER DEFAULT 1,
    terminal_effects INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_privacy (
    user_id INTEGER PRIMARY KEY,
    profile_public INTEGER DEFAULT 1,
    show_country INTEGER DEFAULT 1,
    show_activity INTEGER DEFAULT 1,
    show_xp INTEGER DEFAULT 1,
    show_ranking INTEGER DEFAULT 1,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS security_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    module TEXT NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('low','medium','high','impossible')),
    UNIQUE(user_id, module),
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS guestbook (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT,
    value TEXT
);

CREATE TABLE IF NOT EXISTS api_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    token TEXT,
    version TEXT
);

CREATE TABLE IF NOT EXISTS captcha_challenges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    challenge TEXT,
    answer TEXT,
    used INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    ip TEXT,
    ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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
"""


def seed():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(DDL)

    # Idempotente: só insere se users estiver vazio
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            ("admin", generate_password_hash("password"), "admin"),
        )
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            ("user", generate_password_hash("password"), "user"),
        )
        conn.commit()
        print("[seed] Usuários criados: admin/password, user/password")
    else:
        print("[seed] Usuários já existem — pulando inserção.")

    # Lab data idempotente
    if conn.execute("SELECT COUNT(*) FROM secrets").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO secrets (key, value) VALUES (?,?)",
            [
                ("flag", "DUNO{y0u_f0und_th3_s3cr3t}"),
                ("admin_password", "sup3r_s3cur3_p@ss"),
                ("api_key", "sk-duno-1234567890abcdef"),
            ],
        )
        conn.commit()

    if conn.execute("SELECT COUNT(*) FROM guestbook").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO guestbook (name, message) VALUES (?,?)",
            [
                ("Alice", "Olá, este é o guestbook do DUNO!"),
                ("Bob", "Laboratório de segurança — bem-vindo."),
            ],
        )
        conn.commit()

    if conn.execute("SELECT COUNT(*) FROM api_tokens").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO api_tokens (user_id, token, version) VALUES (?,?,?)",
            [
                (1, "tok-admin-v1-legacy", "v1"),
                (2, "tok-user-v2-current", "v2"),
            ],
        )
        conn.commit()

    if conn.execute("SELECT COUNT(*) FROM captcha_challenges").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO captcha_challenges (challenge, answer) VALUES (?,?)",
            [
                ("Quanto é 3 + 4?", "7"),
                ("Quanto é 5 + 2?", "7"),
                ("Quanto é 8 - 3?", "5"),
            ],
        )
        conn.commit()

    conn.close()
    print(f"[seed] Banco OK: {DB_PATH}")


if __name__ == "__main__":
    seed()
