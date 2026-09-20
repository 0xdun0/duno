# Especificação Oficial: manifest.yml — Máquinas da Comunidade DUNO

O arquivo `manifest.yml` é o contrato descritivo fundamental exigido em qualquer pacote de máquina submetido à plataforma DUNO. Ele define metadados de catálogo, requisitos de runtime, portas de exposição e parâmetros de pontuação de flags.

---

## 1. Localização e Formato

O arquivo deve estar localizado obrigatoriamente na **raiz do pacote compactado** (`.zip` ou `.tar.gz`):

```text
meu-pacote-desafio.zip
├── manifest.yml        <-- Obrigatório na raiz
├── Dockerfile          <-- Ou docker-compose.yml
├── README.md           <-- Writeup e solução técnica
└── src/
```

O arquivo deve ser codificado em **UTF-8** e seguir a sintaxe padrão YAML 1.2.

---

## 2. Estrutura Canônica do Manifesto

```yaml
# =====================================================================
# DUNO Machine Specification Schema v1.0
# =====================================================================

machine:
  name: "Corporate Portal Alpha"
  slug: "alpha-sqli-basics"       # Opcional (se omitido, derivado do name)
  version: "1.0.0"

metadata:
  difficulty: "medium"            # easy | medium | hard | insane
  os: "linux"                     # linux | windows
  category: "web"                 # web | crypto | pwn | reverse | forensic | misc
  short_description: "Laboratório corporativo vulnerável a SQL Injection e bypass de autenticação."
  author:
    name: "CyberLab Team"
    url: "https://github.com/cyberlab"

runtime:
  type: "single"                  # single (Dockerfile) | compose (docker-compose.yml)
  base_image: "python:3.11-slim"
  ports:
    - 5001                        # Portas internas escutadas pelo serviço
  memory_limit: "512m"            # Padrão: 512m
  cpu_limit: "0.5"                # Padrão: 0.5 vCPU

flags:
  - type: "user"
    value: "DUNO{user_flag_alpha_9812}"
    points: 100
  - type: "root"
    value: "DUNO{root_flag_system_alpha_7721}"
    points: 200

writeup:
  solution_file: "README.md"
  hints:
    - "Observe a concatenação de parâmetros na query de login."
    - "O comando ping executa via shell sem sanitização."
```

---

## 3. Descrição dos Campos

### Seção `machine` (Obrigatória)
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | String | **Sim** | Nome de exibição da máquina no catálogo (máx 80 caracteres). |
| `slug` | String | Não | Identificador único URL-friendly (`[a-z0-9\-]`). Se omitido, é gerado do `name`. |
| `version` | String | **Sim** | Versão semântica (ex: `1.0.0`). |

### Seção `metadata` (Obrigatória)
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `difficulty` | Enum | **Sim** | `easy`, `medium`, `hard` ou `insane`. |
| `os` | Enum | **Sim** | `linux` ou `windows`. |
| `category` | Enum | **Sim** | `web`, `crypto`, `pwn`, `reverse`, `forensic`, `misc`. |
| `short_description`| String | **Sim** | Breve resumo didático da máquina (máx 250 caracteres). |
| `author.name` | String | **Sim** | Nome do autor ou equipe criadora. |
| `author.url` | String | Não | Link para perfil público, GitHub ou site. |

### Seção `runtime` (Obrigatória)
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `type` | Enum | Não | `single` (executa via Dockerfile) ou `compose` (usa docker-compose.yml). Padrão: `single`. |
| `ports` | List[Int] | **Sim** | Lista de portas TCP internas escutadas pela máquina. |
| `memory_limit` | String | Não | Teto de memória RAM (máx `1024m`). Padrão: `512m`. |
| `cpu_limit` | String | Não | Fração de CPU reservada (máx `1.0`). Padrão: `0.5`. |

### Seção `flags` (Recomendada)
| Campo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `type` | String | **Sim** | Tipo da flag (ex: `user`, `root`, `flag1`). |
| `value` | String | **Sim** | Valor exato no formato `DUNO{...}`. |
| `points` | Int | **Sim** | Pontuação atribuída ao capturar a flag. |

---

## 4. Regras de Validação Automatizada

Durante a ingestão no Command Center, o validador aplica as seguintes verificações:
1. **Magic Bytes:** O arquivo deve iniciar com assinatura válida de ZIP (`PK\x03\x04`) ou TAR (`\x1f\x8b`).
2. **Presença Obrigatória:** `manifest.yml` e pelo menos um arquivo de entrada (`Dockerfile` ou `docker-compose.yml`).
3. **Varredura Estática:** Rejeição de `privileged: true`, montagens de `/var/run/docker.sock`, uso de `network_mode: host` e credenciais AWS/chaves privadas em texto puro.
