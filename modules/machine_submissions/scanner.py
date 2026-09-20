"""modules/machine_submissions/scanner.py — Análise estática de Dockerfile/Compose e Scanner de Secrets."""
import os
import re
from pathlib import Path

# Padrões para detecção de secrets expostos
SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), "CRITICAL"),
    ("Private Cryptographic Key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "CRITICAL"),
    ("GitHub Token", re.compile(r"\b(ghp_[a-zA-Z0-9]{36}|gho_[a-zA-Z0-9]{36})\b"), "CRITICAL"),
    ("Generic JWT Token", re.compile(r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"), "HIGH"),
    ("Hardcoded Database Password", re.compile(r"(?i)(?:password|passwd|pwd|db_pass)\s*[:=]\s*['\"]([^'\"]{6,})['\"]"), "MEDIUM"),
    ("Slack Webhook", re.compile(r"https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+"), "HIGH")
]

# Regras estáticas de Dockerfile
DOCKERFILE_RULES = [
    ("Docker Socket Mounted", re.compile(r"/var/run/docker\.sock"), "CRITICAL", "docker_socket"),
    ("Privileged Mode", re.compile(r"(?i)--privileged"), "CRITICAL", "privileged"),
    ("Host Network Mode", re.compile(r"(?i)--net(?:work)?\s*=\s*host"), "CRITICAL", "network_mode"),
    ("Host Root Mount", re.compile(r"-v\s+/(?:etc|root|var|home|usr)?:"), "CRITICAL", "mount"),
    ("Elevated Capability", re.compile(r"--cap-add\s+(?:SYS_ADMIN|NET_ADMIN|ALL)"), "HIGH", "capabilities"),
    ("Dangerous Piping", re.compile(r"(?:curl|wget)[^|\n]+|\s*(?:ba)?sh"), "MEDIUM", "dangerous_command"),
    ("Insecure Permissions", re.compile(r"chmod\s+-R\s+777"), "LOW", "permissions"),
]

# Extensões ignoradas no scanner de texto para evitar falsos-positivos em binários
IGNORED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".exe", ".bin", ".tar", ".gz", ".zip"}


def scan_file_for_secrets(filepath: Path, rel_path: str) -> list[dict]:
    """Escaneia um arquivo individual em busca de secrets e credenciais sensíveis."""
    findings = []
    if filepath.suffix.lower() in IGNORED_EXTENSIONS:
        return findings

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, start=1):
                # Limita tamanho da linha para evitar regex DoS
                if len(line) > 2000:
                    continue
                for name, pattern, severity in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append({
                            "severity": severity,
                            "category": "secret",
                            "file_path": rel_path,
                            "line_number": line_idx,
                            "description": f"Possível segredo detectado: {name}",
                            "is_expected": 0,
                            "admin_note": None
                        })
    except Exception:
        pass
    return findings


def scan_dockerfile(filepath: Path, rel_path: str) -> list[dict]:
    """Realiza análise estática nas instruções do Dockerfile."""
    findings = []
    has_user = False
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, start=1):
                line_clean = line.strip()
                if line_clean.startswith("#"):
                    continue

                if line_clean.upper().startswith("USER"):
                    user_val = line_clean.split(maxsplit=1)[-1].strip()
                    if user_val.lower() not in ("root", "0"):
                        has_user = True

                for rule_name, pattern, severity, cat in DOCKERFILE_RULES:
                    if pattern.search(line):
                        findings.append({
                            "severity": severity,
                            "category": cat,
                            "file_path": rel_path,
                            "line_number": line_idx,
                            "description": f"Violação de segurança em Dockerfile: {rule_name}",
                            "is_expected": 0,
                            "admin_note": None
                        })

        if not has_user:
            findings.append({
                "severity": "LOW",
                "category": "root_user",
                "file_path": rel_path,
                "line_number": 1,
                "description": "Container não define usuário não-root (USER). Executa como root por padrão.",
                "is_expected": 0,
                "admin_note": None
            })
    except Exception:
        pass
    return findings


def scan_compose(filepath: Path, rel_path: str) -> list[dict]:
    """Analisa configurações do arquivo docker-compose.yml."""
    findings = []
    try:
        import yaml  # type: ignore
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            data = yaml.safe_load(f)

        if isinstance(data, dict) and "services" in data and isinstance(data["services"], dict):
            for svc_name, svc_cfg in data["services"].items():
                if not isinstance(svc_cfg, dict):
                    continue

                # 1. Privileged
                if svc_cfg.get("privileged") is True:
                    findings.append({
                        "severity": "CRITICAL",
                        "category": "privileged",
                        "file_path": rel_path,
                        "line_number": 1,
                        "description": f"Serviço '{svc_name}' habilitado com 'privileged: true'.",
                        "is_expected": 0,
                        "admin_note": None
                    })

                # 2. Network mode host
                if str(svc_cfg.get("network_mode", "")).lower() == "host":
                    findings.append({
                        "severity": "CRITICAL",
                        "category": "network_mode",
                        "file_path": rel_path,
                        "line_number": 1,
                        "description": f"Serviço '{svc_name}' utiliza 'network_mode: host'.",
                        "is_expected": 0,
                        "admin_note": None
                    })

                # 3. Volumes perigosos
                volumes = svc_cfg.get("volumes", [])
                if isinstance(volumes, list):
                    for v in volumes:
                        v_str = str(v)
                        if "/var/run/docker.sock" in v_str:
                            findings.append({
                                "severity": "CRITICAL",
                                "category": "docker_socket",
                                "file_path": rel_path,
                                "line_number": 1,
                                "description": f"Serviço '{svc_name}' monta o Docker socket do host: {v_str}",
                                "is_expected": 0,
                                "admin_note": None
                            })
                        elif v_str.startswith(("/", "/etc", "/root", "/home")):
                            findings.append({
                                "severity": "HIGH",
                                "category": "mount",
                                "file_path": rel_path,
                                "line_number": 1,
                                "description": f"Serviço '{svc_name}' monta filesystem sensível do host: {v_str}",
                                "is_expected": 0,
                                "admin_note": None
                            })

                # 4. Capabilities perigosas
                cap_add = svc_cfg.get("cap_add", [])
                if isinstance(cap_add, list):
                    for cap in cap_add:
                        if str(cap).upper() in ("SYS_ADMIN", "NET_ADMIN", "ALL"):
                            findings.append({
                                "severity": "HIGH",
                                "category": "capabilities",
                                "file_path": rel_path,
                                "line_number": 1,
                                "description": f"Serviço '{svc_name}' adiciona capability privilegiada: {cap}",
                                "is_expected": 0,
                                "admin_note": None
                            })
    except Exception:
        pass
    return findings


def run_full_security_scan(extracted_dir: str) -> dict:
    """
    Executa varredura estática completa no pacote extraído da máquina.
    Retorna sumário e lista consolidada de findings.
    """
    root_path = Path(extracted_dir)
    findings = []

    # 1. Análise de arquivos Docker e Compose
    dockerfile = root_path / "Dockerfile"
    if dockerfile.is_file():
        findings.extend(scan_dockerfile(dockerfile, "Dockerfile"))

    compose_file = root_path / "docker-compose.yml"
    if not compose_file.is_file():
        compose_file = root_path / "compose.yaml"
    if compose_file.is_file():
        rel_compose = compose_file.name
        findings.extend(scan_compose(compose_file, rel_compose))

    # 2. Varredura de Secrets em todos os arquivos
    for current_dir, _, filenames in os.walk(root_path):
        for fname in filenames:
            fpath = Path(current_dir) / fname
            rel_fpath = str(fpath.relative_to(root_path)).replace("\\", "/")
            findings.extend(scan_file_for_secrets(fpath, rel_fpath))

    # Determina o status consolidado
    has_critical = any(f["severity"] == "CRITICAL" for f in findings)
    has_high = any(f["severity"] == "HIGH" for f in findings)
    has_medium = any(f["severity"] == "MEDIUM" for f in findings)

    if has_critical or has_high:
        status = "failed"
    elif has_medium:
        status = "warnings"
    else:
        status = "passed"

    summary = f"Varredura concluída: {len(findings)} findings encontrados (Críticos: {sum(1 for f in findings if f['severity'] == 'CRITICAL')}, Altos: {sum(1 for f in findings if f['severity'] == 'HIGH')}, Médios: {sum(1 for f in findings if f['severity'] == 'MEDIUM')}, Baixos: {sum(1 for f in findings if f['severity'] == 'LOW')})."

    return {
        "status": status,
        "summary": summary,
        "findings": findings
    }
