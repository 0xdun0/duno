# Banco de Dados SQLite & Schema da Plataforma — DUNO

O **DUNO** utiliza SQLite nativo armazenado em volume persistente (`/app/data/duno.db` ou `data/duno.db`). A aplicação opera sem ORM pesado, utilizando `sqlite3.Row` e `PRAGMA foreign_keys = ON` para máxima velocidade e previsibilidade.

---

## 1. Esquema das Tabelas Principais

### Tabela: `users`
Armazena operadores e credenciais da plataforma:
```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',   -- 'admin' ou 'user'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `security_levels`
Persiste o nível de segurança ativo de cada módulo por usuário:
```sql
CREATE TABLE IF NOT EXISTS security_levels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    level TEXT NOT NULL CHECK(level IN ('low', 'medium', 'high', 'impossible')),
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, module)
);
```

### Tabela: `machine_submissions`
Gerencia a esteira de submissões comunitárias:
```sql
CREATE TABLE IF NOT EXISTS machine_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id),
    category TEXT NOT NULL DEFAULT 'web',
    difficulty TEXT NOT NULL DEFAULT 'medium',
    status TEXT NOT NULL DEFAULT 'draft',
    visibility TEXT NOT NULL DEFAULT 'public',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `machine_versions`
Armazena as versões e arquivos compactados das máquinas:
```sql
CREATE TABLE IF NOT EXISTS machine_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES machine_submissions(id) ON DELETE CASCADE,
    version_str TEXT NOT NULL,
    archive_path TEXT NOT NULL,
    archive_sha256 TEXT NOT NULL,
    manifest_yaml TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'uploaded',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `machine_scans`
Registra os relatórios de análise estática de segurança e linters:
```sql
CREATE TABLE IF NOT EXISTS machine_scans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_id INTEGER NOT NULL REFERENCES machine_versions(id) ON DELETE CASCADE,
    scanner_name TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `machine_audit_logs`
Trilha de auditoria para governança do Command Center:
```sql
CREATE TABLE IF NOT EXISTS machine_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL REFERENCES machine_submissions(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Tabela: `audit_log`
Histórico de ações de segurança, resets e trocas de nível:
```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    ip TEXT NOT NULL,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Rotina de Reset Atômico (`seed.py`)

A qualquer momento, o banco de dados pode ser restaurado para o estado inicial executando:
```bash
docker compose exec duno-app python seed.py
```
Essa rotina:
1. Recria todas as tabelas em transação fechada.
2. Insere os usuários padrão (`admin` e `user`).
3. Define os níveis iniciais (`low` para todos os módulos).
4. Popula o guestbook e dados didáticos de teste.
