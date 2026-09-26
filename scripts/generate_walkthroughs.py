import os
import yaml
import re

yaml_path = 'data/challenges.yaml'
with open(yaml_path, 'r', encoding='utf-8') as f:
    challenges = yaml.safe_load(f)

for item in challenges:
    src_path = item.get('source_path')
    if not src_path or not os.path.exists(src_path):
        continue
    
    walkthrough_dest = os.path.join(src_path, 'walkthrough.md')
    solution_file = os.path.join(src_path, 'solution.md')
    readme_file = os.path.join(src_path, 'README.md')
    
    content = ""
    
    # Se ja existe walkthrough, ok
    if os.path.exists(walkthrough_dest):
        print(f"{src_path} já tem walkthrough.md")
        item['has_walkthrough'] = True
        continue
    
    # Se existe solution.md, copia para walkthrough.md
    if os.path.exists(solution_file):
        with open(solution_file, 'r', encoding='utf-8') as f:
            content = f.read()
    elif os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            readme_text = f.read()
            
        # Tenta encontrar a seção Solution (## Solution ou ## Solution: ou similares)
        match = re.search(r'(?i)(##\s*(Solution|Solução|Resolução|Walkthrough).*?)(?=\n##\s|$)', readme_text, flags=re.DOTALL)
        if match:
            content = match.group(1).strip()
        else:
            print(f"[{src_path}] Seção Solution não encontrada. Adicionando placeholder.")
            content = "# Walkthrough\n\nNenhum walkthrough detalhado fornecido para este desafio."
    else:
        print(f"[{src_path}] Sem README e sem solution.")
        content = "# Walkthrough\n\nWalkthrough pendente."

    # Se conseguiu extrair algo, escreve
    if content:
        with open(walkthrough_dest, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"[{src_path}] walkthrough.md gerado com sucesso.")
    
    item['has_walkthrough'] = True

# Salva YAML atualizado
with open(yaml_path, 'w', encoding='utf-8') as f:
    yaml.dump(challenges, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

print("Processamento concluído. YAML atualizado.")
