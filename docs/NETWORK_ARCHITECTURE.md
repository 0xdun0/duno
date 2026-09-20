# Arquitetura de Redes & Segregação de Ambientes — DUNO

## 1. Visão Geral e Topologia

A infraestrutura de redes do **DUNO** adota um modelo de segregação tripartite padrão **Offensive Security / Red Team**, separando completamente a máquina física do operador, a aplicação de gerenciamento/plataforma e a subnet de execução dos desafios vulneráveis.

```
                         HOST FÍSICO
                    192.168.15.103 (Linux)
                              │
               ┌──────────────┴──────────────┐
               │  duno-net (Bridge Interna)  │ (192.168.100.0/24)
               │                             │
               │  192.168.100.10  duno-app   │
               │  192.168.100.20  c-runner   │
               └──────────────┬──────────────┘
                              │
                     Challenge Runner
                  (Gateway de Controle)
                              │
          ┌───────────────────┴───────────────────┐
          │     challenge-net (Bridge de Ataque)  │ (10.10.15.0/24)
          │                                       │
          │  10.10.15.2   c-runner (Interface)    │
          │  10.10.15.11  Alpha — SQLi Basics     │
          │  10.10.15.12  Bravo — Weak JWT        │
          │  10.10.15.13  Charlie — Cookie Tamper │
          │  10.10.15.14  Cheerio                 │
          │  10.10.15.15  Coffee                  │
          │  10.10.15.xx  ... (Alvos Adicionais)  │
          └───────────────────────────────────────┘
```

---

## 2. Matriz de Redes e Subnets

| Rede | Driver / Tipo | Subnet / Gateway | IP Estático Atribuído | Função no Sistema |
| :--- | :--- | :--- | :--- | :--- |
| **Host** | Físico / eth0 | `192.168.15.0/24` | `192.168.15.103` | Máquina do operador, navegadores e ferramentas externas. |
| **`duno-net`** | Bridge Docker | `192.168.100.0/24`<br>GW: `192.168.100.1` | `192.168.100.10` (`duno-app`)<br>`192.168.100.20` (`challenge-runner`) | Aplicação web principal, SQLite, autenticação, eventos e APIs de controle. |
| **`challenge-net`** | Bridge Docker | `10.10.15.0/24`<br>GW: `10.10.15.1` | `10.10.15.2` (`challenge-runner`)<br>`10.10.15.11` a `.35` (Containers de CTF) | Alvos vulneráveis ativos sob demanda. Escopo de ataque isolado. |

---

## 3. Princípios de Segurança e Isolamento

### A. Impossibilidade de Pivoting Reverso (Alvo $\rightarrow$ Plataforma)
- O container `duno-app` está conectado **exclusivamente** na rede `duno-net` (`192.168.100.0/24`).
- Os alvos vulneráveis estão conectados **exclusivamente** na rede `challenge-net` (`10.10.15.0/24`).
- Se um aluno ou competidor obtiver um **RCE root** no container de um desafio (ex: `10.10.15.11`), varreduras de rede (`nmap -sn 10.10.15.0/24`) e tentativas de tráfego direto para a plataforma (`192.168.100.10`) são descartadas no nível do kernel/bridge Docker. O atacante não tem acesso ao banco de dados nem aos segredos da aplicação.

### B. Bastion / Control Plane (`challenge-runner`)
- O `challenge-runner` é o único serviço que possui interface em ambas as redes (`192.168.100.20` e `10.10.15.2`).
- Ele expõe a API HTTP interna na porta `9000` **apenas** para o `duno-app`, protegida por token criptográfico no header `X-Runner-Token`.
- Não há roteamento de pacotes (ip_forward) ativado dentro do runner; ele opera estritamente como orquestrador via daemon Docker.

---

## 4. Mapeamento Estático de IPs dos Desafios (`10.10.15.0/24`)

Cada laboratório recebe um IP determinístico na subnet `10.10.15.0/24`, tornando a experiência idêntica a plataformas profissionais como Hack The Box e VulnHub:

| ID do Desafio | Nome / Falha | IP Estático | Porta Padrão |
| :--- | :--- | :--- | :--- |
| `alpha-sqli-basics` | Alpha — SQLi Basics | `10.10.15.11` | `5001` |
| `bravo` | Bravo — JWT Broken Auth | `10.10.15.12` | `5000` |
| `charlie-cookie-tampering` | Charlie — Cookie Tampering | `10.10.15.13` | `5000` |
| `cheerio` | Cheerio — Web Exploitation | `10.10.15.14` | `5000` |
| `coffee` | Coffee — Service Exploitation | `10.10.15.15` | `5000` |
| `delta-idor-document-vault` | Delta — IDOR Vault | `10.10.15.16` | `5000` |
| `echo-rate-limit-bypass` | Echo — Rate Limit Bypass | `10.10.15.17` | `5000` |
| `foxtrot-xss-support-tickets`| Foxtrot — Stored XSS | `10.10.15.18` | `5000` |
| `golf-static-analysis-config`| Golf — Static Analysis | `10.10.15.19` | `5000` |
| `hotel-junior-dev-challenge` | Hotel — Web Insecurity | `10.10.15.20` | `3000` |
| `india-nosql-injection` | India — NoSQL Injection | `10.10.15.21` | `5000` |
| `juliet-xxe-injection` | Juliet — XML Entity Injection | `10.10.15.22` | `5000` |
| `kilo-ssti-template-generator`| Kilo — Server-Side Template | `10.10.15.23` | `5000` |
| `lima-deserialization-session`| Lima — Insecure Deserialization | `10.10.15.24` | `5000` |
| `mike-ssrf-to-rce` | Mike — SSRF to RCE | `10.10.15.25` | `5000` |
| `november-drupalgeddon` | November — CMS Exploit | `10.10.15.26` | `80` |
| `oscar-race-conditions` | Oscar — Concurrency Flaws | `10.10.15.27` | `5000` |
| `papa-graphql-injection` | Papa — GraphQL Introspection | `10.10.15.28` | `5000` |
| `quebec-enumeration` | Quebec — Recon & Enum | `10.10.15.29` | `5000` |
| `romeo-dfir-memdump` | Romeo — Memory Forensics | `10.10.15.30` | `5000` |
| `sierra-filing-cabinet` | Sierra — Path Traversal | `10.10.15.31` | `5000` |
| `tango-calculator` | Tango — Code Injection | `10.10.15.32` | `5000` |
| `xray-craftcms-rce` | X-Ray — CMS RCE | `10.10.15.33` | `80` |
| `yankee-log4shell` | Yankee — Log4j / RCE | `10.10.15.34` | `8080` |
| `zulu-koa-devtools` | Zulu — Production DevTools | `10.10.15.35` | `3000` |

---

## 5. Acesso e Roteamento pelo Host Linux

No Linux, qualquer rede criada com o driver `bridge` do Docker instancia automaticamente uma interface de rede no kernel (nome padrão `br-<network_id>`) com o IP do gateway (`10.10.15.1`).

### Rota Direta Automática
O kernel do host cria a rota para toda a subnet `10.10.15.0/24`:
```bash
ip route show | grep 10.10.15
# Saída esperada:
# 10.10.15.0/24 dev br-xxxxxxxxxxxx proto kernel scope link src 10.10.15.1
```

Isso garante que:
1. O aluno pode rodar ferramentas diretamente no terminal do host contra o alvo:
   ```bash
   nmap -sV -sC 10.10.15.11
   curl -I http://10.10.15.11:5001
   python solve.py  # TARGET_URL=http://10.10.15.11:5001
   ```
2. O navegador no host abre diretamente `http://10.10.15.11:5001` sem necessidade de portas efêmeras ou configurações complexas de proxy.

---

## 6. Comandos de Diagnóstico e Validação

### Verificar Redes Criadas
```bash
docker network ls | grep -E "duno-net|challenge-net"
```

### Inspecionar Subnets e Containers Ativos
```bash
docker network inspect duno-net
docker network inspect challenge-net
```

### Validar Roteamento e Conectividade
```bash
# Ping no gateway da rede de laboratório
ping -c 2 10.10.15.1

# Ping em container ativo (quando a máquina estiver ligada)
ping -c 2 10.10.15.11
```
