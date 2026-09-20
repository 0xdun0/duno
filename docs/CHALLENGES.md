# DUNO — Módulo de Desafios CTF

O módulo de **Desafios CTF** do DUNO introduz um laboratório prático de segurança ofensiva baseado em containers Docker isolados e efêmeros sob demanda, com integração ao catálogo de cenários do ctf-challenge.

---

## 1. Arquitetura

O módulo é composto por 3 camadas desacopladas:

1. **Aplicação Web Principal (`duno-app` na porta 2300)**:
   - Renderização SSR pura de catálogo e cards via Jinja2 (`templates/pages/challenges.html`).
   - Download seguro de anexo do guia passo a passo em PDF com proteção estrita a Directory Traversal.
   - Submissão de flag via modal dedicada (removendo poluição visual do card principal).
   - Identificação de Sistema Operacional no card (Linux Tux / Windows Flag) e pontuação em XP com ícone de cristal 💎.
   - Validação server-side de flags com proteção a timing attacks (`secrets.compare_digest`).
   - Rate limiting rígido (30s cooldown, 1 ativo/desafio, 3 total, 3/min/IP, 20/h/user).
   - **Isolamento Total**: O container web NÃO monta `/var/run/docker.sock`.

2. **Challenge Runner (`duno-challenge-runner` na porta 9000)**:
   - Serviço HTTP interno restrito à rede `challenge-control`.
   - Autenticação obrigatória em todas as rotas (exceto `/healthz`) via cabeçalho `X-Runner-Token`.
   - Gerenciamento de ciclo de vida: provisiona containers com limites de recursos (`CPU=0.5`, `MEM=512m`, `PIDS=100`, TTL 60m).
   - Cleanup Worker automatizado para término e remoção de containers expirados.

3. **Rede Isolada de Desafios (`challenge-net`)**:
   - Rede Docker isolada com `internal: true`.
   - Sem roteamento para a rede interna do DUNO (`duno-internal`).
   - Sem conectividade externa (egress desativado por padrão).

---

## 2. Catálogo e Registro de Desafios

Os desafios são cadastrados em `data/challenges.yaml`. Cada desafio deve possuir todos os campos obrigatórios:
- `id` (slug padronizado)
- `name`
- `short_description`
- `category`
- `difficulty` (`beginner`, `easy`, `medium`, `hard`, `insane`)
- `points` (XP)
- `estimated_minutes`
- `os` (`linux` ou `windows`)
- `source_path`
- `environment_type` (`single` ou `compose`)
- `status` (`available`, `maintenance`, `draft`, `deprecated`)
- `attachment_path` (caminho seguro para o PDF do passo a passo)

Validação rigorosa do catálogo via CLI:
```bash
python3 -m modules.challenges.validate_registry data/challenges.yaml
```

---

## 3. Variáveis de Ambiente e Feature Flag

| Variável | Padrão | Descrição |
|---|---|---|
| `CHALLENGES_ENABLED` | `true` | Kill switch do módulo (quando `false`, desativa rotas e links). |
| `CHALLENGE_RUNNER_URL` | `http://challenge-runner:9000` | URL do serviço runner dentro da rede interna. |
| `CHALLENGE_RUNNER_TOKEN` | `duno-runner-secret-key` | Token compartilhado entre web e runner (`X-Runner-Token`). |
| `CHALLENGE_NETWORK` | `challenge-net` | Nome da rede isolada dos containers de desafio. |
| `CHALLENGE_EGRESS_ENABLED` | `false` | Bloqueio padrão de tráfego de saída dos containers. |

---

## 4. Observabilidade e Métricas

O subsistema emite eventos estruturados em formato JSON (logger `duno.ctf.events`) com sanitização de credenciais:
- `challenge_listed`
- `challenge_start_requested`
- `challenge_rate_limited`
- `challenge_started`
- `challenge_start_failed`
- `challenge_stopped`
- `flag_submitted`

Endpoint de métricas consolidado:
```bash
GET /api/challenges/metrics
```

---

## 5. Operação e Rollback

Consulte [`RUNBOOK_ROLLBACK.md`](file:///home/dione/Projects/duno/RUNBOOK_ROLLBACK.md) para procedimentos de desativação emergencial e restauração de dados.
Consulte [`SECURITY_AUDIT.md`](file:///home/dione/Projects/duno/SECURITY_AUDIT.md) para o relatório completo de conformidade de segurança da Seção 19.
