# DUNO — Modules

O DUNO possui 19 módulos de vulnerabilidades web clássicas e um módulo adicional dedicado a API Security.

Todos os módulos integram a mesma aplicação Flask.

## Catálogo

| # | Módulo | Rota | Descrição |
|---:|---|---|---|
| 1 | Brute Force | `/brute_force` | Quebra de autenticação por força bruta. |
| 2 | Command Injection | `/command_injection` | Injeção de comandos através de entrada controlada. |
| 3 | CSRF | `/csrf` | Alteração de estado através de requisição forjada. |
| 4 | File Inclusion | `/file_inclusion` | Inclusão de arquivos através de parâmetro. |
| 5 | File Upload | `/file_upload` | Estudo de upload inseguro. |
| 6 | Insecure CAPTCHA | `/captcha` | Bypass de CAPTCHA. |
| 7 | SQL Injection | `/sqli` | Bypass e manipulação de consultas SQL. |
| 8 | SQL Injection (Blind) | `/sqli_blind` | Cenários boolean-based e time-based. |
| 9 | Weak Session IDs | `/weak_session` | Sessões previsíveis ou manipuláveis. |
| 10 | XSS (DOM) | `/xss_dom` | XSS através do DOM. |
| 11 | XSS (Reflected) | `/xss_reflected` | XSS refletido por parâmetros. |
| 12 | XSS (Stored) | `/xss_stored` | XSS persistido no guestbook. |
| 13 | CSP Bypass | `/csp_bypass` | Estudo de bypass de CSP. |
| 14 | JavaScript Attacks | `/js_attacks` | Manipulação de valores client-side. |
| 15 | Authorisation Bypass | `/auth_bypass` | Acesso indevido a área administrativa. |
| 16 | Open HTTP Redirect | `/open_redirect` | Redirecionamento controlado pelo usuário. |
| 17 | Cryptography | `/crypto` | Estudo de dados considerados protegidos. |
| 18 | API Versioning | `/api_versioning` | Acesso a dados através de versão antiga. |
| 19 | Mass Assignment | `/mass_assignment` | Manipulação de campos através de JSON. |
| 20 | API Security | `/api/*` | Laboratório de segurança de API. |
| 21 | Desafios CTF | `/challenges` | Desafios práticos ofensivos isolados em containers Docker. |

## Estrutura

```text
modules/
├── brute_force/
├── command_injection/
├── csrf/
├── file_inclusion/
├── file_upload/
├── captcha/
├── sqli/
├── sqli_blind/
├── weak_session/
├── xss_dom/
├── xss_reflected/
├── xss_stored/
├── csp_bypass/
├── js_attacks/
├── auth_bypass/
├── open_redirect/
├── crypto/
├── api_versioning/
├── mass_assignment/
└── api_security/
```

## Estrutura interna

Cada módulo segue o padrão:

```text
<module>/
├── __init__.py
├── routes.py
├── logic.py
└── source/
    ├── low.py
    ├── medium.py
    ├── high.py
    └── impossible.py
```

## Fluxo

```text
Dashboard
    ↓
Módulo
    ↓
Security Level
    ↓
Ação do laboratório
    ↓
Lógica correspondente
    ↓
Resultado
```

## API Security

O módulo especial utiliza:

```text
/api/*
```

A documentação original associa a este laboratório conceitos como:

- JWT;
- IDOR;
- Rate Limit;
- versionamento;
- mass assignment.

A implementação detalhada de cada endpoint deve permanecer documentada no próprio módulo.
