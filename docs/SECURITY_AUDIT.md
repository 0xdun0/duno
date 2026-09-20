# RELATÓRIO DE AUDITORIA DE SEGURANÇA — MÓDULO CTF DUNO

Data: 15 de Setembro de 2026  
Escopo: Arquitetura, Contratos e Implementação do Módulo de Desafios Ofensivos CTF (Fases 0 a 5)  
Conformidade: Seção 19 do `upgrade_v3.md`

---

## 1. Matriz de Conformidade com o Checklist de Segurança (Seção 19)

| # | Requisito de Segurança (Seção 19) | Status | Mecanismo de Implementação / Evidência |
|---|---|---|---|
| 1 | Nunca expor os desafios à internet pública | **CONFORME** | Containers rodam na rede Docker interna `challenge-net` com `internal: true`. Apenas a interface de controle do runner escuta internamente em `challenge-control`. |
| 2 | Usar rede Docker dedicada e isolada | **CONFORME** | Rede `challenge-net` configurada como rede dedicada com isolamento estrito sem rota para `duno-internal`. |
| 3 | Impedir acesso dos desafios aos serviços internos do DUNO | **CONFORME** | Os containers dos desafios nunca são anexados à rede `duno-internal` ou `default`. Roteamento inter-redes bloqueado pelo Docker daemon. |
| 4 | Restringir egress para evitar uso como plataforma de ataque | **CONFORME** | A flag `internal: true` na rede `challenge-net` desativa o gateway e roteamento NAT de saída para a internet pública, e `CHALLENGE_EGRESS_ENABLED=false` é padrão no runner. |
| 5 | Não montar diretórios amplos do host nos containers | **CONFORME** | Containers de desafio não recebem volumes do host (exceto o runner que monta estritamente `/opt/challenges:ro` em modo somente leitura). |
| 6 | Não executar containers como privilegiados | **CONFORME** | Nenhuma flag `privileged=True` ou capabilities sensíveis (`SYS_ADMIN`, etc.) são repassadas aos containers em `runner_core.py`. |
| 7 | Aplicar limites de CPU, memória, processos e execução | **CONFORME** | `CPU_LIMIT=0.5` (`nano_cpus=500_000_000`), `MEM_LIMIT="512m"`, `PIDS_LIMIT=100` e TTL padrão de 3600s com término automático. |
| 8 | Parar e remover instâncias automaticamente ao expirar | **CONFORME** | `Cleanup Worker` no `runner_core.py` executa varreduras a cada 30s purgando instâncias cujo timestamp `expires_at` tenha sido atingido. |
| 9 | Validar todos os IDs e caminhos por allowlist | **CONFORME** | IDs validados contra o catálogo em memória via `SLUG_REGEX`; resolução de caminhos usando `Path.is_relative_to(BASE_DIR)` impedindo Directory Traversal (`../`). |
| 10 | Proteger ações de escrita com autenticação e CSRF | **CONFORME** | Endpoints de `instances` e `submit` exigem `@login_required` e validação de `X-CSRFToken` com `secrets.compare_digest`. |
| 11 | Não exibir stack traces ou segredos ao cliente | **CONFORME** | Mensagens de erro de API são padronizadas e tratadas (`jsonify({"error": msg})`); flags e tokens nunca são vazados. |
| 12 | O web app não monta o socket do Docker | **CONFORME** | `duno-app` não possui volume `/var/run/docker.sock`. Toda comunicação com o Docker é intermediada via HTTP interno com token autenticado para `challenge-runner`. |
| 13 | Comparação de flag resistente a timing attacks | **CONFORME** | Verificação com `secrets.compare_digest` em `flag_service.py`. |
| 14 | Prevenção de pontuação duplicada / race conditions | **CONFORME** | Constraint `UNIQUE(user_id, challenge_id)` na tabela `challenge_solves` com tratamento de concorrência atômica. |
| 15 | Download seguro de anexo do guia (PDF) com proteção a Directory Traversal | **CONFORME** | Rota `/challenges/<id>/attachment` valida isolamento de path com `is_relative_to(BASE_DIR)` antes de servir com `as_attachment=True`. |
| 16 | Isolamento de recursos dos containers | **CONFORME** | CPU (0.5), Memória (512MB), PIDs (100) e rede isolada `challenge-net` sem acesso à rede do app. |
| 17 | Desativação segura via Feature Flag | **CONFORME** | `CHALLENGES_ENABLED=false` oculta navegação e bloqueia rotas com 404 e APIs com 503. |

---

## 3. Matriz de Testes Automatizados Implementados

- `test_challenge_catalog.py`: Validação de esquema YAML, campos obrigatórios (`os`, `attachment_path`), unicidade de IDs e bloqueio de Traversal.
- `test_challenge_attachment.py`: Verificação de download de PDF, proteção contra Path Traversal, autenticação e cabeçalhos `application/pdf`.
- `test_challenge_runner.py`: Comunicação com runner HTTP, token secreto obrigatório, idempotência, isolamento do Docker socket e TTL.
- `test_challenge_solves.py`: Submissão de flags, prevenção contra timing attacks (`compare_digest`), controle de duplicatas e concorrência SQLite.
- `test_challenge_routes.py`: Autenticação de rotas web, renderização SSR inicial de catálogo, badges de SO e XP, e validação de CSRF.
- `test_challenge_production.py`: Comportamento sob Feature Flag desativada, backup/restore de catálogo e exportação de dados.olamento de pontuação.

Todos os 45 testes encontram-se 100% verdes.
