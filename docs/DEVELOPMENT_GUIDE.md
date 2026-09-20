# Como Desenvolver Novos Módulos de Vulnerabilidade — DUNO

Este guia orienta engenheiros e pesquisadores de segurança na implementação de novos laboratórios de vulnerabilidade web nativos no DUNO.

---

## 1. Estrutura de um Módulo OWASP

Para criar um novo módulo (ex: `modules/ssti/`), crie os seguintes arquivos:

```text
modules/ssti/
├── __init__.py           # Exporta o Blueprint Flask bp
├── routes.py             # Rotas de interface e API do laboratório
├── logic.py              # Regra de negócio dos 4 níveis
└── source/               # Código didático para o modal de inspeção
    ├── low.py
    ├── medium.py
    ├── high.py
    └── impossible.py
```

---

## 2. Passo a Passo de Implementação

### Passo 1: Inicialização do Blueprint (`__init__.py`)
```python
from flask import Blueprint

bp = Blueprint("ssti", __name__, url_prefix="/ssti")

from . import routes  # noqa: E402, F401
```

### Passo 2: Roteamento & Template (`routes.py`)
```python
from flask import render_template, request, session
from core.decorators import login_required
from core.security_levels import get_level
from . import bp
from .logic import execute_payload

@bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    user_id = session.get("user_id", 1)
    level = get_level(user_id, "ssti")
    output = ""
    if request.method == "POST":
        payload = request.form.get("name", "")
        output = execute_payload(payload, level)
    return render_template("modules/ssti.html", level=level, output=output)
```

### Passo 3: Graduação Lógica nos 4 Níveis (`logic.py`)
```python
def check_low(template_str):
    # Sem sanitização (Vulnerável)
    return f"Olá, {template_str}"

def check_medium(template_str):
    # Filtro fraco de palavras-chave
    banned = ["config", "self"]
    for b in banned:
        template_str = template_str.replace(b, "")
    return f"Olá, {template_str}"

def check_high(template_str):
    # Sanitização com whitelist de caracteres
    import re
    cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", template_str)
    return f"Olá, {cleaned}"

def check_impossible(template_str):
    # Escape seguro de templates (Jinja2 autoescape nativo)
    from markupsafe import escape
    return f"Olá, {escape(template_str)}"

def execute_payload(payload, level):
    handlers = {
        "low": check_low,
        "medium": check_medium,
        "high": check_high,
        "impossible": check_impossible
    }
    handler = handlers.get(level, check_low)
    return handler(payload)
```

### Passo 4: Registro no Sistema
1. Registre o slug em `core/security_levels.py` na lista `VALID_MODULES`.
2. Registre o Blueprint em `app/__init__.py` na função `_register_blueprints`.
3. Adicione o link de navegação na dropdown `LABS` em `templates/base.html`.
4. Crie testes automatizados em `tests/` verificando se o nível `low` é explorável e `impossible` é seguro.
