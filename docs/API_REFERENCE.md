# Referência de APIs REST & Endpoints do Sistema — DUNO

O DUNO expõe endpoints HTTP RESTful para automação de desafios, telemetria pedagógica do Kids e submissão de máquinas comunitárias.

---

## 1. Endpoints de Desafios CTF (`/api/challenge/*`)

### `POST /api/challenge/start`
Inicializa uma máquina de desafio sob demanda.
* **Headers:** `Content-Type: application/json`
* **Payload:**
  ```json
  {
    "challenge_id": "alpha-sqli-basics"
  }
  ```
* **Resposta (200 OK):**
  ```json
  {
    "status": "success",
    "instance_id": "inst-a1b2c3d4",
    "port": 4001,
    "url": "http://localhost:4001",
    "expires_at": "2026-09-20T01:15:00Z",
    "time_remaining_seconds": 2700
  }
  ```

### `POST /api/challenge/stop`
Para e remove uma instância em execução.
* **Payload:** `{"instance_id": "inst-a1b2c3d4"}`
* **Resposta:** `{"status": "stopped"}`

### `POST /api/challenge/submit-flag`
Valida a submissão de uma flag capturada pelo operador.
* **Payload:**
  ```json
  {
    "challenge_id": "alpha-sqli-basics",
    "flag": "DUNO{user_flag_alpha_9812}"
  }
  ```
* **Resposta:**
  ```json
  {
    "correct": true,
    "points_awarded": 100,
    "message": "Flag capturada com sucesso!"
  }
  ```

---

## 2. Endpoints do DUNO Kids (`/kids/api/*`)

### `POST /kids/api/lab/execute`
Executa comandos no simulador de terminal CRT ou valida desafios de sequenciamento.
* **Payload:**
  ```json
  {
    "lesson_id": "os-terminal-intro",
    "type": "terminal",
    "command": "ls -la"
  }
  ```
* **Resposta:**
  ```json
  {
    "output": "total 4\n-rwxr-xr-x 1 tux tux 42 key.txt",
    "completed": true,
    "tux_reaction": "Excelente! Você listou os arquivos ocultos!"
  }
  ```

### `POST /kids/api/quiz/answer`
Valida resposta de múltipla escolha no Checkpoint de uma missão.
* **Payload:**
  ```json
  {
    "quiz_id": 12,
    "answer": "B"
  }
  ```
* **Resposta:**
  ```json
  {
    "correct": true,
    "explanation": "O comando pwd significa Print Working Directory.",
    "lives_remaining": 3,
    "tux_reaction": "Sensacional! Você acertou de primeira!"
  }
  ```

---

## 3. Endpoints de Submissões & Auditoria (`/submissions/api/*`)

### `GET /submissions/api/list`
Lista máquinas submetidas pelo usuário autenticado.

### `POST /submissions/api/upload`
Recebe o pacote compactado `.zip` ou `.tar.gz` da máquina (máx 50MB).

### `GET /api/docs/search?q=<termo>`
Mecanismo de busca textual e indexação da documentação técnica.
* **Parâmetro:** `q` (termo de busca)
* **Resposta:**
  ```json
  [
    {
      "slug": "quickstart",
      "title": "Getting Started & Setup Rápido",
      "category_title": "Get started",
      "desc": "Como subir o DUNO via Docker Compose...",
      "icon": "nf-md-rocket_launch",
      "snippet": "...Clone o repositório oficial git clone..."
    }
  ]
  ```
