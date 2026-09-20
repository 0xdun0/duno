# DUNO — Designed Unsecure Network Operations

Plataforma unificada para treinamento prático de segurança ofensiva, pentest web, exploração de APIs e auditoria de contêineres vulneráveis.

## Visão Geral

O DUNO reúne em uma única interface modular ambientes práticos de exploração de vulnerabilidades, desafios estilo CTF (Capture The Flag) isolados em contêineres Docker, esteira de auditoria para submissão de máquinas da comunidade e uma trilha didática para iniciantes (DUNO Kids).

### Stack Tecnológica

- **Backend**: Python 3.11+ / Flask 3.x
- **Banco de Dados**: SQLite com schema padronizado (`data/duno.db`)
- **Frontend**: HTML5 semântico, CSS Vanilla modular (Walkie Minimal Design System), JavaScript Vanilla
- **Orquestração**: Docker / Docker Compose
- **Isolamento de Alvos**: Subnet tripartite e `challenge-runner` REST API

---

## Estrutura da Plataforma

### 1. Módulos Clássicos OWASP (20 Laboratórios)

Cada laboratório possui 4 níveis de mitigação gradual (**Low**, **Medium**, **High**, **Impossible**), permitindo comparar falhas reais com código corrigido:

| # | Módulo | Rota | Descrição Técnica |
|---:|---|---|---|
| 1 | Brute Force | `/brute_force` | Autenticação vulnerável a dicionário e rate-limit progressivo |
| 2 | Command Injection | `/command_injection` | Execução de comandos no SO via concatenação de inputs |
| 3 | CSRF | `/csrf` | Falsificação de requisições cross-site e validação de tokens SameSite |
| 4 | File Inclusion | `/file_inclusion` | Local File Inclusion (LFI) e Directory Traversal com wrappers |
| 5 | File Upload | `/file_upload` | Upload malicioso com bypass de MIME type, extensão e magic bytes |
| 6 | Insecure CAPTCHA | `/captcha` | Validação de captcha em client-side e bypass de parâmetros |
| 7 | SQL Injection | `/sqli` | Injeção SQL inline com union-based extraction |
| 8 | SQL Injection (Blind) | `/sqli_blind` | Extração por inferência booleana e time-based payloads |
| 9 | Weak Session IDs | `/weak_session` | Previsibilidade e entropia de tokens de sessão |
| 10 | XSS (DOM) | `/xss_dom` | Execução client-side através de sinks vulneráveis no DOM |
| 11 | XSS (Reflected) | `/xss_reflected` | Refletido imediato via parâmetros de URL sem sanitização |
| 12 | XSS (Stored) | `/xss_stored` | Armazenamento persistente em banco e renderização desprotegida |
| 13 | CSP Bypass | `/csp_bypass` | Injeção contornando diretivas permissivas de Content-Security-Policy |
| 14 | JavaScript Attacks | `/js_attacks` | Manipulação e tamper de variáveis client-side |
| 15 | Authorisation Bypass | `/auth_bypass` | Quebra de controle de acesso (BOLA/IDOR) e escalação de privilégio |
| 16 | Open HTTP Redirect | `/open_redirect` | Redirecionamento aberto e validação por lista de permissões |
| 17 | Cryptography | `/crypto` | Fraquezas em cifras, modos de operação e seeds de aleatoriedade |
| 18 | API Versioning | `/api_versioning` | Quebra de integridade através de endpoints legados `/api/v1` |
| 19 | Mass Assignment | `/mass_assignment` | Modificação de propriedades de modelo não autorizadas (ex: role) |
| 20 | API Security | `/api/*` | Endpoints REST com JWT, CORS permissivo e falhas de rate limit |

### 2. Challenge Runner & CTF Engine

- Execução de alvos dinâmicos em contêineres Docker independentes na rede `duno-challenges-net`.
- Temporizador regressivo de 45 a 60 minutos por instância com encerramento automático.
- Submissão de flags dinâmicas validadas em banco de dados SQLite.

### 3. Esteira de Submissão de Máquinas da Comunidade

- Upload seguro de pacotes `.zip` e `.tar.gz` com inspeção estrita de integridade.
- Proteções contra **ZipSlip**, **ZipBomb** (limite rígido de 100MB descompactado) e **proibição total de symlinks e hardlinks**.
- Validação estrutural de `manifest.yml` e scanner automatizado de `Dockerfile` (bloqueio de `--privileged`, montagem de `/var/run/docker.sock` e network `host`).
- Command Center administrativo para auditoria, aprovação e publicação de novos desafios.

### 4. DUNO Kids & Terminal CRT

- Ambiente lúdico com mascote institucional para introdução prática à segurança e fundamentos de computação.
- Emulador de Terminal Linux CRT com histórico de comandos, sistema de arquivos virtual e desafios progressivos.

---

## Início Rápido

### Pré-requisitos

- Docker 24.0+
- Docker Compose v2+

### Inicialização do Ambiente

```bash
# 1. Clonar repositório
git clone <repository-url>
cd duno

# 2. Inicializar contêineres
docker compose up --build -d
```

A plataforma estará pronta em:

```text
http://localhost:2300
```

Credenciais administrativas padrão de laboratório:
- **Usuário**: `admin`
- **Senha**: `password`

### Comandos de Manutenção

```bash
# Exibir logs da aplicação
docker compose logs -f duno-app

# Parar contêineres e encerrar redes
docker compose down

# Rodar a suite completa de testes automatizados
pytest tests/ -v
```

---

## Documentação Técnica

O projeto conta com uma Central de Documentação integrada e navegável diretamente na aplicação através da rota:

```text
GET /docs
```

Os guias técnicos originais estão organizados em `docs/`:

### Get Started
- [Getting Started & Setup Rápido](docs/QUICKSTART.md) — Inicialização via Docker Compose, portas e credenciais.
- [Visão Geral da Arquitetura](docs/ARCHITECTURE.md) — Componentes do core, fluxos de autenticação e containers.
- [Estrutura de Diretórios & Convenções](docs/DIRECTORY_STRUCTURE.md) — Organização de pastas, templates e módulos.

### Guias & Prática
- [DUNO Kids: Currículo & Terminal CRT](docs/KIDS_CURRICULUM.md) — 5 trilhas didáticas e emulador CRT.
- [Walkthrough de Pentest: Alpha SQLi](docs/WALKTHROUGH_ALPHA.md) — Metodologia de exploração passo a passo.
- [Como Desenvolver Novos Módulos](docs/DEVELOPMENT_GUIDE.md) — Criação de desafios Low a Impossible.
- [Guia de Empacotamento & Submissão de Máquinas](docs/MACHINE_SUBMISSIONS.md) — Pipeline de auditoria e validação de pacotes.

### Manuais & Arquitetura
- [Topologia de Redes & Segregação Tripartite](docs/NETWORK_ARCHITECTURE.md) — Isolamento de host, app e subnet de alvos.
- [Orquestração de Desafios & Challenge Runner](docs/CHALLENGES.md) — Gerenciamento dinâmico de instâncias Docker.
- [Banco de Dados SQLite & Schema](docs/DATABASE_SCHEMA.md) — DDL, tabelas, migrações e persistência.
- [Política de Segurança, Sandbox & Uso Responsável](docs/SECURITY_POLICY.md) — Hardening anti-ZipSlip/ZipBomb e regras de sandbox.
- [Runbook de Operações & Rollback](docs/RUNBOOK_ROLLBACK.md) — Procedimentos emergenciais de contingência.
- [Identidade Visual & Design System](docs/DESIGN_SYSTEM.md) — Diretrizes Walkie Minimal e tokens de CSS.

### Referência Técnica
- [Especificação Oficial do manifest.yml](docs/MANIFEST_SPEC.md) — Schema obrigatório para submissão de máquinas.
- [Catálogo dos 20 Módulos de Vulnerabilidade](docs/MODULES.md) — Rotas, vetores de injeção e proteções.
- [Graduação dos Níveis de Segurança](docs/SECURITY_LEVELS.md) — Diferenciação conceitual e técnica dos 4 níveis.
- [Referência de APIs REST & Endpoints](docs/API_REFERENCE.md) — Especificação dos endpoints `/api/*`.
- [What's New & Changelog](docs/CHANGELOG.md) — Linha do tempo das versões e melhorias da plataforma.

---

## Itens Pendentes de Padronização (Débito Técnico)

Para assegurar total transparência no ciclo de desenvolvimento, os seguintes componentes estão listados como pendentes de alinhamento com os padrões vigentes da plataforma:

1. **Templates de Módulos Legados**:
   - Alguns laboratórios Web mais antigos (ex: `Insecure CAPTCHA`, `Weak Session IDs`) ainda possuem trechos de estilização inline ou fragmentos herdados que não utilizam integralmente as classes e tokens do Design System Walkie Minimal (`duno.css`).
2. **Desacoplamento de Lógica Frontend**:
   - Determinados formulários clássicos mantêm manipulação de eventos via atributos `onsubmit`/`onclick` embutidos no HTML, devendo ser refatorados para event listeners isolados em arquivos JS modulares.
3. **Unificação do Runner de Desafios**:
   - Os 20 módulos OWASP nativos rodam dentro do processo do `duno-app`, enquanto os novos desafios da comunidade operam no serviço isolado `challenge-runner`. Planeja-se migrar gradualmente todos os módulos práticos para instâncias isoladas.
4. **Padronização de Ícones**:
   - Todos os elementos visuais devem utilizar estritamente classes NerdFonts (`nf-*`) ou SVGs inline parametrizados na paleta padrão, eliminando qualquer dependência de imagens auxiliares estáticas fora de contexto.

---

## Aviso de Segurança & Uso Responsável

O DUNO contém vulnerabilidades deliberadas e mecanismos de execução de comandos controlados.

- Execute a plataforma **exclusivamente em contêineres Docker isolados**.
- **Nunca exponha a porta `2300` diretamente para redes públicas ou ambientes de produção**.
- **Não armazene credenciais reais ou dados sensíveis** dentro dos bancos de teste do laboratório.
