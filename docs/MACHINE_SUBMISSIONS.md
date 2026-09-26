# Guia Completo de Desenvolvimento & Empacotamento de Máquinas CTF

O **DUNO** permite que qualquer desenvolvedor, pesquisador de segurança ou instrutor crie e submeta máquinas de laboratório para a comunidade. 

Quando aprovada pela equipe de curadoria no painel administrativo, a máquina é **implantada automaticamente no Challenge Runner**, entra no **catálogo oficial de Desafios CTF**, dispara uma **notificação no sino da navbar** para os alunos e recebe o selo **`NOVA MÁQUINA`** até ser visualizada.

---

## 1. Como uma Máquina Funciona no DUNO

Cada máquina no DUNO roda como um **container Docker isolado** sob demanda:
1. O usuário clica em **Start Machine** no card do desafio.
2. O **Challenge Runner** compila a imagem Docker (`duno-img-machine-<slug>`) a partir dos arquivos enviados e sobe o container isolado na rede `challenge-net` com um IP dedicado (ex: `10.10.15.xx`).
3. O aluno recebe o IP e a porta mapeada para iniciar os testes (via navegador web, netcat, terminal ou VPN).
4. Ao capturar as flags (`user` ou `root`), o usuário submete no card e os pontos são creditados instantaneamente.

---

## 2. Liberdade de Criação: Tecnologias e Vetores de Ataque

> [!IMPORTANT]
> **Crie Cenários Originais:** Não reutilize nomes, slugs ou credenciais de máquinas já existentes no DUNO. Cada máquina deve trazer sua própria temática, identidade visual e vetores de exploração.

O seu laboratório **não precisa ser apenas Web nem usar PHP**. Você pode construir desafios explorando qualquer ecossistema tecnológico e qualquer técnica ofensiva:

* **Aplicações Web & APIs:** Python (Flask/FastAPI/Django), Node.js (Express/Koa), PHP, Go, Ruby on Rails, Java (Spring Boot), ASP.NET Core.  
  *Vulnerabilidades:* SSRF, SSTI, SQL Injection, IDOR, Broken Authentication, Deserialização Insegura, Race Conditions, GraphQL Injection, File Inclusion/Upload.
* **Escalação de Privilégios (PrivEsc):**  
  *Vetores:* Binários com permissão SUID/SGID, permissões permissivas no `sudoers`, tarefas agendadas via cron jobs com scripts graváveis, Linux Capabilities mal configuradas, Path Hijacking, credenciais em logs ou histórico `.bash_history`.
* **Binary Exploitation (Pwn) & Reverse Engineering:**  
  *Serviços:* Binários C/C++ expostos via `socat` ou SSH em portas dedicadas (ex: 1337, 2222, 9001).  
  *Vulnerabilidades:* Stack Overflow, Format String, Ret2libc, ROP, lógica reversa de executáveis.
* **Criptografia & Misconfigurations:**  
  *Vetores:* Chaves privadas expostas, uso de cifras fracas, bypass de tokens JWT assinados com chaves simétricas triviais, bancos NoSQL/Redis expostos sem autenticação.

---

## 3. Estrutura Obrigatória do Pacote

O pacote deve ser um arquivo compactado `.zip` ou `.tar.gz` (máximo de 50MB) com a seguinte organização:

```text
minha-maquina.zip
├── manifest.yml          # Especificação técnica, metadados e flags (obrigatório)
├── Dockerfile            # Arquivo de build do container Docker (obrigatório)
├── entrypoint.sh         # Script de inicialização e serviços (recomendado)
├── README.md             # Documentação técnica e writeup didático da solução
└── app/                  # Código-fonte, binários ou scripts da máquina vulnerável
```

---

## 4. Especificação do `manifest.yml`

O arquivo `manifest.yml` na raiz é o coração da máquina. Ele define limites de hardware, portas, objetivos educacionais e os hashes das flags:

```yaml
version: "1.0.0"
name: "Nome da Sua Máquina"                # Nome público de exibição (único e temático)
slug: "nome-da-sua-maquina"                # Slug identificador em minúsculas (a-z, 0-9, hífen)
description: "Breve resumo do cenário vulnerável e do objetivo principal do desafio."
author: "seu_usuario"                      # Seu usuário ou handle na plataforma
difficulty: "medium"                       # easy, medium, hard, insane
os: "linux"                                # linux, windows
category: "web"                            # web, pwn, crypto, recon, forensics, api

runtime:
  type: "single"                           # container único
  base_image: "debian:bookworm-slim"       # Qualquer imagem base segura (Ubuntu, Alpine, Debian, Node, Python, etc.)
  ports:
    - 8080                                 # Porta primária exposta (ex: 80, 8080, 5000, 1337)
  memory_limit: "512m"                     # 256m, 512m, 1024m
  cpu_limit: "0.5"                         # 0.5 = 50% de um núcleo de CPU

flags:
  user:
    flag: "FLAG{sua_flag_de_usuario_aleatoria_12345}"
    points: 100
    location: "/home/usuario_alvo/user.txt"
  root:
    flag: "FLAG{sua_flag_de_root_final_segura_67890}"
    points: 200
    location: "/root/root.txt"

educational:
  objectives:
    - "Identificar a falha primária de entrada na aplicação ou serviço exposto"
    - "Obter acesso interativo (shell) com privilégios reduzidos"
    - "Explorar a vulnerabilidade local configurada para obter privilégios de root"
  prerequisites:
    - "Fundamentos de redes e exploração do protocolo em questão"
    - "Comandos básicos de terminal Linux e enumeração de permissões"
  hints:
    - "Primeira dica sutil sem spoiler direto."
    - "Segunda dica para destravar a elevação de privilégios."
```

---

## 5. Passo a Passo Prático: Construindo sua Máquina

### Passo 1: O `Dockerfile`
O container deve conter todos os serviços necessários para a máquina rodar de forma autônoma. Substitua os nomes de usuário, binários e pacotes conforme o enredo do seu desafio:

```dockerfile
FROM debian:bookworm-slim

# Instala pacotes do sistema necessários para o seu cenário
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Cria usuário de baixa permissão específico da sua temática (evite nomes genéricos ou duplicados)
RUN useradd -m -s /bin/bash usuario_alvo

# Implanta a flag de usuário (com permissão somente leitura para o usuário criado)
RUN echo "FLAG{sua_flag_de_usuario_aleatoria_12345}" > /home/usuario_alvo/user.txt && \
    chown usuario_alvo:usuario_alvo /home/usuario_alvo/user.txt && \
    chmod 600 /home/usuario_alvo/user.txt

# Implanta a flag de root (acessível exclusivamente pelo superusuário)
RUN echo "FLAG{sua_flag_de_root_final_segura_67890}" > /root/root.txt && \
    chmod 600 /root/root.txt

# Exemplo de configuração de vetor de escalação de privilégios intencional
# (Pode ser um binário customizado, capability, cron job, sudoers, script mal configurado, etc.)
RUN echo "usuario_alvo ALL=(ALL) NOPASSWD: /usr/bin/python3 /opt/scripts/backup.py" >> /etc/sudoers

# Copia os arquivos da sua aplicação / serviço
COPY app/ /opt/app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Porta exposta para o aluno conectar
EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
```

### Passo 2: O `entrypoint.sh`
O entrypoint inicia serviços auxiliares e **deve manter o processo principal no foreground** para que o container permaneça ativo durante a sessão do laboratório:

```bash
#!/bin/bash
set -e

# Inicializa serviços em background caso seu cenário precise (ex: banco, socat, cron, ssh)
# service cron start
# service mariadb start

echo "[+] Inicializando serviços do desafio..."

# Inicia a aplicação principal no primeiro plano (foreground)
# Substitua pelo comando da sua stack (ex: python, node, gunicorn, socat, apache)
exec python3 /opt/app/server.py
```

### Passo 3: Testando Localmente Antes do Envio
Valide se o container compila e responde adequadamente com os limites da plataforma:

```bash
# 1. Compila a imagem Docker localmente
docker build -t test-nome-da-maquina .

# 2. Executa simulando os limites de CPU e memória
docker run --rm -d -p 8080:8080 --memory 512m --cpus 0.5 --name ctf-local-test test-nome-da-maquina

# 3. Testa a conectividade no serviço exposto
curl http://localhost:8080
# Ou se for um serviço TCP/Pwn: nc localhost 8080

# 4. Encerra o container de teste
docker stop ctf-local-test
```

### Passo 4: Empacotando o Pacote ZIP Sanitizado
Gere o `.zip` garantindo que não contenha lixo de versionamento ou arquivos locais de IDE:

```bash
zip -r nome-da-sua-maquina.zip . -x "*.git*" "*__pycache__*" "*.DS_Store*" "*.vscode*" "*.idea*"
```

---

## 6. Como Submeter na Plataforma

1. Acesse o **Command Center** no menu superior do DUNO (`/command-center` ou no menu de usuário).
2. Vá até a aba **Minhas Contribuições** e clique em **Nova Submissão de Máquina**.
3. Preencha o nome, categoria, dificuldade e anexe o seu arquivo `.zip` ou `.tar.gz`.
4. A esteira automatizada executará:
   * **Gate 1 (Anti-Malware & Integridade):** Análise contra ZipSlip, magic bytes e verificação de symlinks maliciosos.
   * **Gate 2 (Varredura de Segurança):** Scanner AST em busca de montagens do Docker socket ou privilégios indevidos contra o host.
   * **Gate 3 (Moderação Administrativa):** A submissão fica disponível para a equipe técnica aprovar.

---

## 7. O que Acontece Após a Aprovação

Ao ser aprovada por um administrador:
1. **Extração Automática:** Os arquivos são implantados na pasta de desafios ativos (`challenges/machine-<slug>/`).
2. **Entrada no Catálogo:** O card aparece imediatamente em `/challenges` com pontos e tags calculados.
3. **Notificação Global:** O sino de notificações na barra superior é ativado para todos os alunos informando a chegada da nova máquina.
4. **Badge de Destaque:** O card exibe o selo **`NOVA MÁQUINA`** para cada usuário que ainda não abriu o desafio.
5. **Pontuação no Ranking:** As flags resolvidas pelos estudantes são contabilizadas normalmente no placar geral.

---

## 8. Regras Estritas de Segurança (Evitando Rejeição)

Para proteger a integridade do servidor hospedeiro, máquinas que contenham as seguintes práticas serão **rejeitadas sumariamente**:
* ❌ Montagem do Docker Socket hospedeiro (`/var/run/docker.sock`).
* ❌ Modos de rede host (`network_mode: host`).
* ❌ Containers privilegiados (`privileged: true` ou `CAP_SYS_ADMIN` sem isolamento estrito).
* ❌ Montagens de diretórios raiz do servidor hospedeiro (`/`, `/etc`, `/root`, `/home`).
* ❌ Links simbólicos (symlinks) apontando para fora da árvore do pacote compactado.
* ❌ Scripts que baixam artefatos ou se comunicam com servidores de comando e controle (C2) externos reais.
