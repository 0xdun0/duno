"""modules/challenges/validate_registry.py — Validação rígida do catálogo de desafios."""
import sys
import os
import re
from pathlib import Path
import yaml

from modules.challenges.catalog import (
    VALID_DIFFICULTIES,
    VALID_ENVIRONMENTS,
    VALID_STATUSES,
    VALID_PROTOCOLS,
    SLUG_REGEX,
    get_registry_path,
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def validate_registry(registry_path=None):
    """Executa a validação completa do catálogo contra as regras da Seção 8 do upgrade_v3.md."""
    path = Path(registry_path) if registry_path else get_registry_path()
    errors = []
    warnings = []

    if not path.exists():
        return False, [f"Arquivo de catálogo não encontrado: {path}"], []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return False, [f"Erro de sintaxe YAML: {e}"], []

    if not isinstance(data, list):
        return False, ["O catálogo deve ser uma lista de desafios."], []

    seen_ids = set()
    used_ports = {}

    for idx, item in enumerate(data, start=1):
        prefix = f"Desafio #{idx}"
        if not isinstance(item, dict):
            errors.append(f"{prefix}: Formato inválido (esperado mapeamento).")
            continue

        cid = item.get("id", "")
        prefix = f"Desafio '{cid or idx}'"

        # 1. Validação de ID / Slug
        if not cid or not isinstance(cid, str):
            errors.append(f"{prefix}: 'id' é obrigatório e deve ser string.")
        elif not SLUG_REGEX.match(cid):
            errors.append(f"{prefix}: 'id' contém caracteres inválidos (deve seguir padrão slug: letras minúsculas, números e hífens).")
        elif cid in seen_ids:
            errors.append(f"{prefix}: ID duplicado '{cid}'.")
        seen_ids.add(cid)

        # 2. Resolução de caminho seguro
        source_path_str = item.get("source_path", "")
        if not source_path_str:
            errors.append(f"{prefix}: 'source_path' obrigatório.")
            source_dir = None
        else:
            resolved_source = (BASE_DIR / source_path_str).resolve()
            if not resolved_source.is_relative_to(BASE_DIR):
                errors.append(f"{prefix}: 'source_path' fora da raiz permitida do projeto (path traversal detectado).")
                source_dir = None
            elif not resolved_source.exists() or not resolved_source.is_dir():
                errors.append(f"{prefix}: Diretório do desafio não encontrado: {source_path_str}")
                source_dir = None
            else:
                source_dir = resolved_source

        # 3. Tipo de ambiente & Dockerfile / Compose
        env_type = item.get("environment_type", "").lower()
        if env_type not in VALID_ENVIRONMENTS:
            errors.append(f"{prefix}: 'environment_type' inválido '{env_type}'. Opções: {VALID_ENVIRONMENTS}")
        elif source_dir:
            dockerfile = source_dir / "Dockerfile"
            compose = source_dir / "docker-compose.yml"
            if env_type == "single" and not dockerfile.exists():
                errors.append(f"{prefix}: Ambiente 'single' exige 'Dockerfile' na pasta do desafio.")
            elif env_type == "compose" and not compose.exists():
                errors.append(f"{prefix}: Ambiente 'compose' exige 'docker-compose.yml' na pasta do desafio.")

        # 4. Portas internas
        port = item.get("internal_port")
        if port is not None:
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"{prefix}: 'internal_port' deve ser número inteiro entre 1 e 65535.")
            else:
                if port in used_ports:
                    warnings.append(f"{prefix}: Porta interna {port} compartilhada com '{used_ports[port]}'. (Válido em containers isolados, mas requer atenção em portas expostas no host).")
                used_ports[port] = cid

        # 5. Dificuldade e Status
        diff = item.get("difficulty", "").lower()
        if diff not in VALID_DIFFICULTIES:
            errors.append(f"{prefix}: 'difficulty' inválida '{diff}'. Opções: {VALID_DIFFICULTIES}")

        status = item.get("status", "").lower()
        if status not in VALID_STATUSES:
            errors.append(f"{prefix}: 'status' inválido '{status}'. Opções: {VALID_STATUSES}")

        # 6. Sistema Operacional (linux ou windows)
        challenge_os = item.get("os", "linux").lower()
        if challenge_os not in ("linux", "windows"):
            errors.append(f"{prefix}: 'os' inválido '{challenge_os}'. Opções: ('linux', 'windows')")

        # 7. Pontos e tempo estimado
        pts = item.get("points")
        if pts is None or not isinstance(pts, int) or pts < 0:
            errors.append(f"{prefix}: 'points' deve ser inteiro >= 0.")

        est = item.get("estimated_minutes")
        if est is None or not isinstance(est, int) or est <= 0:
            errors.append(f"{prefix}: 'estimated_minutes' deve ser inteiro > 0.")

        # 8. Campos obrigatórios de texto
        if not item.get("name"):
            errors.append(f"{prefix}: 'name' é obrigatório.")
        if not item.get("short_description"):
            errors.append(f"{prefix}: 'short_description' é obrigatória.")
        if not item.get("category"):
            errors.append(f"{prefix}: 'category' é obrigatória.")

    return len(errors) == 0, errors, warnings


def main():
    print("Iniciando validação do catálogo de desafios CTF...")
    registry_file = get_registry_path()
    print(f"Catálogo alvo: {registry_file}")
    ok, errors, warnings = validate_registry(registry_file)

    for w in warnings:
        print(f"  [AVISO] {w}")

    if not ok:
        print(f"\n[FALHA] Foram encontrados {len(errors)} erro(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)

    print(f"\n[SUCESSO] Catálogo validado com êxito! Todos os itens respeitam a especificação.")
    sys.exit(0)


if __name__ == "__main__":
    main()
