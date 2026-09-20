# Getting Started & Guia de Início Rápido — DUNO

Bem-vindo ao **DUNO**, a plataforma moderna e deliberadamente vulnerável de cibersegurança ofensiva, simulação de adversários e treinamento técnico.

---

## 1. Pré-Requisitos do Sistema

O DUNO foi arquitetado para ser completamente conteinerizado. Você não precisa instalar dependências do Python, compiladores ou bancos de dados na sua máquina hospedeira.

* **Sistema Operacional:** Linux (recomendado), macOS ou Windows 11 com WSL2.
* **Docker Engine:** Versão 24.0 ou superior (`docker --version`).
* **Docker Compose:** Plugin v2 (`docker compose version`) ou `docker-compose`.
* **Memória RAM:** Mínimo de 4GB recomendados (para suportar instâncias simultâneas de CTF).
* **Portas Livres:** `2300` (Aplicação Principal) e range `4001-4025` (Desafios Dinâmicos).

---

## 2. Inicialização em Um Comando

Para inicializar a plataforma com compilação automática de assets, injeção de sementes no banco SQLite e volumes persistentes:

```bash
# Clone o repositório oficial
git clone https://github.com/eudionelima/duno.git
cd duno

# Inicialize os containers via Docker Compose
docker compose up --build -d
```

Verifique se o serviço está saudável através dos logs:

```bash
docker compose logs -f duno-app
```

---

## 3. Acesso à Interface & Credenciais Padrão

Após a inicialização do container, abra seu navegador web:

* **URL da Aplicação:** [http://localhost:2300](http://localhost:2300)
* **Usuário Padrão:** `admin`
* **Senha Padrão:** `password`

> [!NOTE]
> O usuário `admin` possui permissões de operador global, acesso ao **Command Center**, visualização de logs de auditoria e moderação de máquinas da comunidade.

---

## 4. Estrutura dos Módulos Principais

Ao ingressar no Dashboard principal, você encontrará os 4 grandes pilares do DUNO:

1. **Laboratórios OWASP (20 Módulos):** Laboratórios graduais com 4 níveis de segurança (Low, Medium, High e Impossible) e visualizador interativo de código-fonte.
2. **DUNO Kids (5 Trilhas Gamificadas):** Interface pedagógica com simulador de terminal CRT Linux, quizzes com feedback do Tux e analogias práticas.
3. **Challenges CTF (25 Máquinas):** Máquinas reais executadas em containers efêmeros isolados com expiração automática em 45 minutos.
4. **Command Center:** Painel de controle de máquinas da comunidade, parâmetros de segurança, telemetria e auditoria.

---

## 5. Reset Global do Banco de Dados

Como os laboratórios sofrem ataques reais de SQL Injection, alteração de tabelas e inserção de payloads XSS, o DUNO possui uma rotina de restauração atômica idempotente.

Você pode restaurar o banco a qualquer momento:
* **Via Interface:** Clique no menu do seu perfil no canto superior direito e selecione **Reset Database**.
* **Via Terminal / Shell:**
  ```bash
  docker compose exec duno-app python seed.py
  ```

---

## 6. Próximos Passos

* Leia a [Visão Geral da Arquitetura](/docs/architecture) para entender o isolamento de processos.
* Conheça o [Currículo do DUNO Kids](/docs/kids-curriculum) para treinar comandos Linux essenciais.
* Explore o catálogo de [Desafios CTF](/docs/challenges-engine) para praticar invasões reais em ambientes isolados.
