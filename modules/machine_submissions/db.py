"""modules/machine_submissions/db.py — DDL e inicialização de tabelas do Sistema de Submissão de Máquinas."""
import sqlite3
import json
from datetime import datetime

SUBMISSIONS_DDL = """
-- 1. Cabeçalho de submissões
CREATE TABLE IF NOT EXISTS machine_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(status IN (
        'DRAFT','SUBMITTED','TRIAGE','BUILDING','SECURITY_REVIEW',
        'FUNCTIONAL_TEST','CONTENT_REVIEW','APPROVED','PUBLISHED',
        'CHANGES_REQUESTED','REJECTED','UNPUBLISHED','ARCHIVED'
    )),
    current_version TEXT DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 2. Versões da máquina
CREATE TABLE IF NOT EXISTS machine_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    version_str TEXT NOT NULL,
    package_path TEXT,
    extracted_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(submission_id, version_str),
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE
);

-- 3. Metadados técnicos e educacionais
CREATE TABLE IF NOT EXISTS machine_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    short_desc TEXT NOT NULL,
    full_desc TEXT,
    os_type TEXT NOT NULL DEFAULT 'Linux',
    os_distro TEXT,
    architecture TEXT NOT NULL DEFAULT 'amd64',
    author_difficulty TEXT NOT NULL DEFAULT 'Medium',
    reviewed_difficulty TEXT,
    difficulty_reason TEXT,
    category TEXT NOT NULL DEFAULT 'Web',
    objectives_json TEXT,       -- Array JSON de objetivos
    prerequisites_json TEXT,    -- Array JSON de pré-requisitos
    skills_developed TEXT,
    scenario_intro TEXT,
    hints_json TEXT,            -- Array JSON de hints
    references_json TEXT,       -- Array JSON de referências
    walkthrough_md TEXT,        -- Walkthrough/solução do autor em Markdown (opcional)
    exposed_ports_json TEXT,    -- Array JSON de portas expostas
    cpu_limit REAL DEFAULT 1.0,
    memory_limit_mb INTEGER DEFAULT 1024,
    disk_limit_mb INTEGER DEFAULT 5120,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 4. Arquivos do pacote da máquina
CREATE TABLE IF NOT EXISTS machine_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    is_critical INTEGER DEFAULT 0,
    sha256 TEXT,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 5. Builds isolados
CREATE TABLE IF NOT EXISTS machine_builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    build_number INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued','running','success','failed','timeout','cancelled')),
    exit_code INTEGER,
    duration_seconds REAL DEFAULT 0.0,
    image_tag TEXT,
    image_size_mb REAL,
    logs TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 6. Sessões de varredura de segurança
CREATE TABLE IF NOT EXISTS machine_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    scan_type TEXT NOT NULL, -- static_analysis, secrets_scanner, dependency_scan
    status TEXT NOT NULL DEFAULT 'passed' CHECK(status IN ('running','passed','warnings','failed')),
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 7. Findings de segurança
CREATE TABLE IF NOT EXISTS machine_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER,
    version_id INTEGER NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('CRITICAL','HIGH','MEDIUM','LOW','INFO')),
    category TEXT NOT NULL,
    file_path TEXT,
    line_number INTEGER,
    description TEXT NOT NULL,
    is_expected INTEGER DEFAULT 0,
    admin_note TEXT,
    status TEXT DEFAULT 'open' CHECK(status IN ('open','acknowledged','resolved')),
    FOREIGN KEY(scan_id) REFERENCES machine_scans(id) ON DELETE SET NULL,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 8. Testes funcionais e de runtime
CREATE TABLE IF NOT EXISTS machine_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL,
    test_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'passed' CHECK(status IN ('passed','failed','running','skipped')),
    details TEXT,
    duration_ms INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 9. Flags verificadas (sem expor segredos em texto plano)
CREATE TABLE IF NOT EXISTS machine_flags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    version_id INTEGER NOT NULL,
    flag_type TEXT NOT NULL CHECK(flag_type IN ('user','root','secret')),
    flag_hash TEXT NOT NULL,
    is_present INTEGER DEFAULT 1,
    location_hint TEXT,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(version_id) REFERENCES machine_versions(id) ON DELETE CASCADE
);

-- 10. Revisões finais e decisões
CREATE TABLE IF NOT EXISTS machine_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    version_id INTEGER,
    reviewer_id INTEGER NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('APPROVED','CHANGES_REQUESTED','REJECTED')),
    reason TEXT,
    category TEXT, -- Security, Runtime, Functionality, Educational, Policy, Other
    scorecard_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(reviewer_id) REFERENCES users(id)
);

-- 11. Comentários e comunicação autor/revisor
CREATE TABLE IF NOT EXISTS machine_review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    author_role TEXT NOT NULL DEFAULT 'user', -- author, reviewer, admin
    comment_text TEXT NOT NULL,
    is_resolved INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 12. Histórico de estados da submissão
CREATE TABLE IF NOT EXISTS machine_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by_user_id INTEGER,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id) ON DELETE CASCADE,
    FOREIGN KEY(changed_by_user_id) REFERENCES users(id)
);

-- 13. Auditoria dedicada da esteira de máquinas
CREATE TABLE IF NOT EXISTS machine_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    resource TEXT NOT NULL,
    resource_id TEXT,
    status TEXT DEFAULT 'SUCCESS',
    ip TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- 14. Máquinas publicadas no catálogo ativo
CREATE TABLE IF NOT EXISTS published_machines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL UNIQUE,
    challenge_id TEXT NOT NULL UNIQUE,
    published_version TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unpublished_at TIMESTAMP,
    FOREIGN KEY(submission_id) REFERENCES machine_submissions(id)
);

-- 15. Notificações globais da plataforma (Novas máquinas, avisos de sistema)
CREATE TABLE IF NOT EXISTS platform_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL DEFAULT 'machine_published',
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT,
    target_id TEXT,
    target_role TEXT,
    target_user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 16. Controle de leitura de notificações por usuário
CREATE TABLE IF NOT EXISTS user_notification_reads (
    user_id INTEGER NOT NULL,
    notification_id INTEGER NOT NULL,
    read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, notification_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(notification_id) REFERENCES platform_notifications(id) ON DELETE CASCADE
);

-- 17. Registro de visualização de desafios por usuário (Para controle do badge NOVA MÁQUINA)
CREATE TABLE IF NOT EXISTS user_challenge_views (
    user_id INTEGER NOT NULL,
    challenge_id TEXT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, challenge_id),
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Índices de performance e consulta
CREATE INDEX IF NOT EXISTS idx_machine_sub_user ON machine_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_machine_sub_status ON machine_submissions(status);
CREATE INDEX IF NOT EXISTS idx_machine_sub_slug ON machine_submissions(slug);
CREATE INDEX IF NOT EXISTS idx_machine_ver_sub ON machine_versions(submission_id);
CREATE INDEX IF NOT EXISTS idx_machine_findings_ver ON machine_findings(version_id);
CREATE INDEX IF NOT EXISTS idx_machine_findings_sev ON machine_findings(severity);
CREATE INDEX IF NOT EXISTS idx_machine_comments_sub ON machine_review_comments(submission_id);
CREATE INDEX IF NOT EXISTS idx_machine_audit_act ON machine_audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_notifs_created ON platform_notifications(created_at);
"""


def init_submissions_db(db: sqlite3.Connection):
    """Executa a DDL de submissão de máquinas no banco de dados SQLite."""
    try:
        db.executescript(SUBMISSIONS_DDL)
        # Migração defensiva para colunas de role/user em platform_notifications
        cols = [r[1] for r in db.execute("PRAGMA table_info(platform_notifications)").fetchall()]
        if "target_role" not in cols:
            db.execute("ALTER TABLE platform_notifications ADD COLUMN target_role TEXT")
        if "target_user_id" not in cols:
            db.execute("ALTER TABLE platform_notifications ADD COLUMN target_user_id INTEGER")
        # Migração defensiva para o walkthrough do autor
        meta_cols = [r[1] for r in db.execute("PRAGMA table_info(machine_metadata)").fetchall()]
        if "walkthrough_md" not in meta_cols:
            db.execute("ALTER TABLE machine_metadata ADD COLUMN walkthrough_md TEXT")
        db.commit()
    except Exception as e:
        print(f"[WARN] Erro inicializando tabelas de submissões: {e}")


def create_platform_notification(
    db: sqlite3.Connection,
    ntype: str,
    title: str,
    message: str,
    link: str | None = None,
    target_id: str | None = None,
    target_role: str | None = None,
    target_user_id: int | None = None
) -> int | None:
    """Cria uma nova notificação do sistema para a plataforma ou escopo de usuário/role."""
    try:
        cur = db.execute(
            """INSERT INTO platform_notifications (type, title, message, link, target_id, target_role, target_user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (ntype, title, message, link, target_id, target_role, target_user_id)
        )
        db.commit()
        return cur.lastrowid
    except Exception as e:
        print(f"[WARN] Erro ao criar notificação: {e}")
        return None


def log_machine_audit(db: sqlite3.Connection, user_id: int | None, action: str, resource: str, resource_id: str | None = None, status: str = "SUCCESS", ip: str | None = None, metadata: dict | None = None):
    """Registra uma operação crítica no log de auditoria de máquinas."""
    try:
        meta_str = json.dumps(metadata) if metadata else None
        db.execute(
            """INSERT INTO machine_audit_logs (user_id, action, resource, resource_id, status, ip, metadata_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, action, resource, resource_id, status, ip, meta_str)
        )
        db.commit()
    except Exception as e:
        print(f"[WARN] Erro ao gravar machine_audit_log: {e}")
