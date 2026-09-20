# Estrutura de Diretórios & Convenções Técnicas — DUNO

O **DUNO** foi desenhado com base no princípio de **responsabilidade única**, modularidade estrita e zero-bloat. A plataforma não utiliza frameworks CSS pesados ou ORMs intrusivos, garantindo controle total sobre cada byte transmitido.

---

## 1. Visão Geral da Árvore de Diretórios

```text
duno/
├── app/                      # Application Factory & Rotas Globais da Aplicação
│   └── __init__.py           # create_app(), registro de blueprints e interceptors
├── core/                     # Núcleo de Infraestrutura e Serviços Compartilhados
│   ├── auth.py               # Sessão nativa, hashing de senhas e RBAC
│   ├── database.py           # Conexão SQLite (sqlite3.Row, foreign_keys=ON)
│   ├── decorators.py         # Decorators @login_required e @admin_required
│   ├── docs_manager.py       # Parser de Markdown, catálogo e busca da documentação
│   ├── reset.py              # Mecanismo atômico de Reset do Banco
│   ├── security_levels.py    # Gerenciamento de níveis Low/Medium/High/Impossible
│   └── source_loader.py      # Carregamento seguro de fontes para o modal de código
├── modules/                  # 20 Módulos de Vulnerabilidade OWASP e Subsistemas
│   ├── brute_force/          # Módulo 01: Quebra de autenticação por força bruta
│   ├── sqli/                 # Módulo 07: SQL Injection clássico & bypass
│   ├── challenges/           # Catálogo, orquestração e gerenciamento de CTFs
│   ├── kids/                 # Subsistema DUNO Kids (5 Trilhas, Lab CRT & Quizzes)
│   ├── machine_submissions/  # Esteira de submissões comunitárias e auditoria
│   │   ├── validator.py      # Proteção anti-ZipSlip/ZipBomb e schema do manifest
│   │   ├── scanner.py        # Análise estática de Dockerfile/compose e segredos
│   │   ├── state_machine.py  # Máquina de estados (Draft -> Scanning -> Published)
│   │   ├── routes.py         # Portal do autor de máquinas
│   │   └── admin_routes.py   # Command Center e moderação administrativa
│   └── ... (demais 18 módulos OWASP)
├── challenges/               # Repositório dos 25 Desafios CTF Ofensivos
│   ├── alpha-sqli-basics/    # Desafio 01: SQLi em portal corporativo
│   ├── bravo/                # Desafio 02: Bypass de autenticação e OTP
│   ├── charlie-cookie-tampering/ # Desafio 03: Falsificação de cookies e sessões
│   └── ... (25 desafios completos)
├── static/                   # Assets Estáticos da Plataforma
│   ├── css/
│   │   ├── duno.css          # Design System Walkie/Obsidian
│   │   └── kids.css          # Estilos gamificados para o Duno Kids
│   ├── js/
│   │   ├── duno.js           # Visualizador de código, typewriter e busca
│   │   └── kids.js           # Controlador do Terminal CRT e Mascote Tux
│   └── img/                  # Logos, badges e diagramas
├── templates/                # Templates HTML Jinja2
│   ├── base.html             # Shell global com Header, Navbar e Footer
│   ├── index.html            # Dashboard principal com catálogo de módulos
│   ├── pages/                # Páginas estáticas e hub de documentação (docs.html)
│   ├── kids/                 # Telas do Kids (dashboard, missão, lab e quiz)
│   └── submissions/          # Telas de submissão e visualização de máquinas
├── docs/                     # Repositório Central de Documentação Técnica (.md)
├── data/                     # Volume persistente do SQLite (duno.db)
├── tests/                    # Suíte de Testes Automatizados (pytest)
├── config.py                 # Configurações de ambiente, limites e paths
├── docker-compose.yml        # Orquestração do duno-app e duno-challenges-net
└── requirements.txt          # Dependências Python mínimas congeladas
```

---

## 2. Convenção de Módulos de Vulnerabilidade

Cada laboratório OWASP sob `modules/<nome>/` obedece a uma arquitetura padrão em 4 camadas:

1. `__init__.py`: Instancia e expõe o Blueprint Flask (`bp = Blueprint(...)`).
2. `routes.py`: Roteamento HTTP, renderização de templates e validação de formulários.
3. `logic.py`: Regra de negócio contendo as 4 funções de validação correspondentes a cada nível de segurança:
   * `check_low(param)`
   * `check_medium(param)`
   * `check_high(param)`
   * `check_impossible(param)`
4. `source/`: Diretório contendo os 4 arquivos de código-fonte reais exibidos no modal didático do operador:
   * `low.py` (código vulnerável, sem sanitização)
   * `medium.py` (filtro ingênuo ou bypassável)
   * `high.py` (controles rígidos)
   * `impossible.py` (implementação canônica e segura)

---

## 3. Segurança nos Diretórios de Execução

* **Permissões de Diretório:** Arquivos gerados durante a execução operam sob permissão `0o644` e diretórios sob `0o755`.
* **Banco de Dados:** O arquivo do banco vive obrigatoriamente dentro de `data/duno.db`, montado como volume dedicado para não sofrer perdas durante o rebuild de containers.
* **Isolamento de Desafios:** Cada pasta em `challenges/<slug>/` é completamente independente, contendo seu próprio `Dockerfile`, dependências e script de inicialização (`app.py` / `entrypoint.sh`).
