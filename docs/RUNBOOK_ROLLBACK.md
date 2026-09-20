# RUNBOOK: Procedimento de Rollback e Desativação Emergencial — Módulo CTF DUNO

Este documento descreve os procedimentos operacionais padrão para desativação imediata do subsistema de desafios CTF ou reversão completa das alterações em ambiente de produção/staging.

---

## 1. Desativação Imediata (Kill Switch via Feature Flag — Zero Deploy)

Se houver suspeita de comprometimento, sobrecarga de recursos ou instabilidade no ambiente de desafios:

### Passo 1: Alterar a variável de ambiente
No arquivo `.env` da raiz do DUNO:
```bash
CHALLENGES_ENABLED=false
```

### Passo 2: Notificar os containers
Se rodando via Docker Compose:
```bash
docker compose exec duno-app export CHALLENGES_ENABLED=false
# Ou recarregar as variáveis:
docker compose up -d --no-recreate duno-app
```

### Efeito Imediato:
- A rota `/challenges` e `/challenges/<id>/attachment` passa a responder `404 Not Found`.
- Todas as APIs sob `/api/challenges/*` respondem imediatamente `503 Service Unavailable` com status `disabled`.
- O link `CHALLENGES` na barra de navegação superior desaparece automaticamente via template condition (`challenges_enabled=False`).
- Nenhuma nova instância de container pode ser criada.

---

## 2. Purga e Interrupção Emergencial de Containers de Desafio

Para forçar a interrupção imediata de todos os containers de laboratório CTF ativos:

```bash
# 1. Listar containers de desafios em execução
docker ps --filter "name=duno-ctf-" --format "{{.ID}} - {{.Names}}"

# 2. Interromper e remover forçadamente todos os containers de desafios
docker rm -f $(docker ps -aq --filter "name=duno-ctf-") 2>/dev/null || true

# 3. Interromper o serviço challenge-runner se necessário
docker compose stop challenge-runner
```

---

## 3. Reversão e Limpeza de Banco de Dados (SQLite)

Caso seja necessário purgar os dados transacionais de instâncias e soluções de desafios:

```bash
# Backup preventivo do banco antes de qualquer operação destrutiva:
cp /app/data/duno.db /app/data/duno.db.bak_$(date +%Y%m%d_%H%M%S)

# Executar purge das tabelas CTF mantendo os usuários e demais módulos intactos:
sqlite3 /app/data/duno.db <<EOF
BEGIN TRANSACTION;
DROP TABLE IF EXISTS challenge_solves;
DROP TABLE IF EXISTS challenge_instances;
DELETE FROM audit_log WHERE action LIKE 'challenge_%';
COMMIT;
EOF
```

---

## 4. Restauração do Catálogo e Flags a partir de Backup

Para restaurar o catálogo de desafios e flags a partir de uma cópia snapshot:

```bash
# Via Python:
python3 -c "from modules.challenges.backup import restore_registry; restore_registry('/caminho/do/backup')"

# Ou manualmente:
cp /caminho/do/backup/challenges.yaml data/challenges.yaml
cp /caminho/do/backup/flags.yaml data/flags.yaml
python3 -m modules.challenges.validate_registry
```

---

## 5. Checklist de Verificação pós-Rollback

- [ ] `curl -s -o /dev/null -w "%{http_code}" http://localhost:2300/challenges` retorna `404`.
- [ ] `curl -s -X POST http://localhost:2300/api/challenges/hotel-junior-dev-challenge/instances` retorna `503`.
- [ ] `docker ps | grep duno-ctf-` retorna vazio.
- [ ] O monolito principal do DUNO (módulos 1 a 20 e Academy) continua 100% operacional.
