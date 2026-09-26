"""
DUNO Academy — Security Knowledge Engine
Structured pedagogical knowledge base for all 20 DUNO laboratory challenges.
"""
import yaml
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _load_academy_data():
    try:
        from flask_babel import get_locale
        locale = str(get_locale())
    except Exception:
        locale = "pt"
    
    yaml_path = DATA_DIR / f"academy_{locale}.yaml"
    if not yaml_path.exists():
        yaml_path = DATA_DIR / "academy_base.yaml"
        
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        with open(DATA_DIR / "academy_base.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

def get_learning_paths():
    return _load_academy_data().get('paths', [])

def get_all_lessons_summary():
    data = _load_academy_data()
    all_modules = data.get('modules', [])
    lessons = data.get('lessons', {})
    
    items = []
    for m in all_modules:
        num, title, slug, path_id, path_name, desc, rtime, diff = m
        has_deep_dive = slug in lessons
        items.append({
            "num": num,
            "title": title,
            "slug": slug,
            "path_id": path_id,
            "path_name": path_name,
            "desc": desc,
            "read_time": rtime,
            "difficulty": diff,
            "has_deep_dive": has_deep_dive
        })
    return items

def get_lesson_data(slug):
    data = _load_academy_data()
    lessons = data.get('lessons', {})
    if slug in lessons:
        return lessons[slug]
        
    summary_list = get_all_lessons_summary()
    item = next((x for x in summary_list if x["slug"] == slug), None)
    if not item:
        return None

    return {
        "num": item["num"],
        "slug": item["slug"],
        "title": item["title"],
        "subtitle": f"Dissecando as falhas conceituais, vetores de ataque e defesas aplicadas a {item['title']}.",
        "path_id": item["path_id"],
        "path_name": item["path_name"],
        "read_time": item["read_time"],
        "difficulty": item["difficulty"],
        "lab_endpoint": f"{slug}.index",
        "overview": f"O módulo {item['title']} explora vulnerabilidades críticas de {item['path_name']}. {item['desc']} No laboratório DUNO, você experimenta na prática como a ausência de controle compromete a integridade do sistema.",
        "why_it_happens": "A falha surge quando a camada de negócio assume premissas não verificadas sobre o tráfego de entrada, delegando segurança a camadas externas ou aplicando validações incompletas que não cobrem os limites do protocolo.",
        "how_it_works": f"O fluxo de exploração em {item['title']} manipula requisições legítimas para forçar o backend a processar estados não previstos, expondo dados internos ou concedendo privilégios indevidos.",
        "diagram_steps": [
            {"step": "01", "name": "Input / Requisição", "desc": "Parâmetro manipulado enviado para o endpoint"},
            {"step": "02", "name": "Processamento Frágil", "desc": "Aplicação avalia dados sem validação estrita"},
            {"step": "03", "name": "Execução Insegura", "desc": "Componente interno processa ação fora dos limites de segurança"},
            {"step": "04", "name": "Impacto Observado", "desc": "Bypass de controle, extração de dados ou execução não autorizada"}
        ],
        "anatomy": [
            {"label": "INPUT", "content": f"Dados submetidos no endpoint /modules/{slug}."},
            {"label": "PROCESSING", "content": "Fluxo de validação no controller sem checagem de limites."},
            {"label": "VULNERABLE COMPONENT", "content": f"Mecanismo de controle de {item['title']}."},
            {"label": "OUTPUT", "content": "Comportamento divergente do esperado em sistemas seguros."}
        ],
        "recognition": "Análise de respostas HTTP, códigos de status inesperados e inspeção do código-fonte através do motor 'View Source'.",
        "attack_concept": f"Pratique no laboratório DUNO observando o comportamento nos níveis LOW, MEDIUM e HIGH antes de testar a defesa IMPOSSIBLE.",
        "vulnerable_code": f"# Código representativo do desafio {item['title']}\n@bp.route('/modules/{slug}')\ndef handler():\n    data = request.args.get('input')\n    return process_insecurely(data)",
        "security_levels": [
            {"level": "LOW", "status": "Vulnerável", "desc": "Implementação sem qualquer barreira de proteção."},
            {"level": "MEDIUM", "status": "Mitigação Parcial", "desc": "Filtros superficiais facilmente contornáveis."},
            {"level": "HIGH", "status": "Defesa Reforçada", "desc": "Regras mais estritas mas ainda com brechas de arquitetura."},
            {"level": "IMPOSSIBLE", "status": "Seguro", "desc": "Arquitetura robusta aplicando o princípio de menor privilégio e validação estrita."}
        ],
        "before_after": {
            "vulnerable": "# Inseguro: processa entrada arbitrária sem controle\nexecute_action(user_input)",
            "secure": "# Seguro: valida e aplica controle estrito\nif is_valid(user_input): execute_secure(user_input)"
        },
        "defense": f"A correção de {item['title']} exige a implementação de defesas em profundidade (Defense-in-Depth), nunca confiando em validações unilaterais ou verificações superficiais de formato.",
        "secure_code": f"# Implementação Segura para {item['title']}\ndef safe_handler():\n    validated = strict_validator(request.form)\n    return process_securely(validated)",
        "common_mistakes": [
            "Assumir que dados enviados pelo navegador são legítimos.",
            "Implementar verificações com regex fracas ou incompletas.",
            "Tratar apenas os sintomas sem corrigir a causa raiz na arquitetura."
        ],
        "quiz": {
            "question": f"Qual é o princípio fundamental para prevenir falhas no módulo {item['title']}?",
            "options": [
                "Validar e sanitizar estritamente os dados no servidor aplicando o princípio do menor privilégio",
                "Desativar mensagens de log do servidor",
                "Mudar o nome dos arquivos e parâmetros no front-end",
                "Confiar apenas na validação de formulários com JavaScript no navegador"
            ],
            "correct_index": 0,
            "explanation": "A validação rigorosa no servidor aliada ao menor privilégio é o pilar indispensável para garantir que entradas maliciosas não comprometam a aplicação."
        },
        "checklist": [
            f"Compreender a causa raiz de {item['title']}.",
            "Inspecionar o código fonte real no laboratório via View Source.",
            "Comparar a evolução entre os 4 níveis de segurança.",
            "Aplicar as melhores práticas defensivas documentadas."
        ]
    }
