"""modules/machine_submissions/validator.py — Validação de pacotes de máquinas, manifest.yml e proteção contra ZipSlip, ZipBomb e Symlinks."""
import os
import zipfile
import tarfile
import hashlib
import yaml  # type: ignore
from pathlib import Path

MAX_PACKAGE_FILES = 500
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024  # 100 MB
MAX_SINGLE_FILE_BYTES = 60 * 1024 * 1024   # 60 MB
MAX_COMPRESSION_RATIO = 100
REQUIRED_MANIFEST_SECTIONS = ("machine", "metadata", "runtime")

# Dispositivos reservados do Windows e nomes de sistema
RESERVED_NAMES = {
    "con", "prn", "aux", "nul",
    "com1", "com2", "com3", "com4", "com5", "com6", "com7", "com8", "com9",
    "lpt1", "lpt2", "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"
}


class ValidationError(Exception):
    """Exceção levantada quando um pacote ou manifesto é inválido."""
    pass


def compute_sha256(filepath: str | Path) -> str:
    """Calcula o hash SHA256 de um arquivo."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_archive_magic_bytes(filepath: str | Path) -> str:
    """
    Inspeciona os primeiros bytes do arquivo para garantir que se trata
    de um arquivo ZIP ou TAR/GZ legítimo e não um arquivo executável mascarado.
    """
    if not os.path.isfile(filepath):
        raise ValidationError("Arquivo de pacote não encontrado.")
    
    with open(filepath, "rb") as f:
        header = f.read(512)

    if header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06") or header.startswith(b"PK\x07\x08"):
        return "zip"
    if header.startswith(b"\x1f\x8b"):
        return "tar.gz"
    if len(header) >= 262 and header[257:262] == b"ustar":
        return "tar"
    
    raise ValidationError("Assinatura de arquivo inválida (magic bytes). O arquivo deve ser um pacote .zip ou .tar.gz legítimo.")


def _sanitize_and_check_path(filename: str, dest_path: Path) -> Path:
    """
    Verifica se o nome de arquivo não contém caracteres perigosos,
    não tenta path traversal e está estritamente contido em dest_path.
    """
    if "\x00" in filename:
        raise ValidationError(f"Caractere nulo detectado no nome do arquivo: {filename!r}")
    
    # Normaliza separadores de caminho
    norm_name = filename.replace("\\", "/").strip("/")
    parts = norm_name.split("/")

    for p in parts:
        if p in ("..", ""):
            raise ValidationError(f"Tentativa de Path Traversal ('..') detectada no arquivo: {filename}")
        p_base = p.split(".")[0].lower()
        if p_base in RESERVED_NAMES:
            raise ValidationError(f"Nome reservado de dispositivo detectado: {p}")

    target_file = (dest_path / norm_name).resolve()
    try:
        target_file.relative_to(dest_path)
    except ValueError:
        raise ValidationError(f"Tentativa de Path Traversal detectada fora do diretório de extração: {filename}")

    return target_file


def safe_extract_zip(archive_path: str | Path, extract_to: str | Path) -> list[dict]:
    """
    Extrai arquivo .zip com mitigação contra:
    1. ZipSlip (Path Traversal via relative_to)
    2. Zip Bomb (limite de arquivos, contagem de bytes descompactados em streaming)
    3. Symlink / Hardlink attacks (rejeição de atributos POSIX de links simbólicos)
    4. Sanitização de permissões (0o644 para arquivos, 0o755 para diretórios)
    """
    validate_archive_magic_bytes(archive_path)

    dest_path = Path(extract_to).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    total_uncompressed_bytes = 0
    file_count = 0

    with zipfile.ZipFile(archive_path, 'r') as zf:
        infolist = zf.infolist()
        if len(infolist) > MAX_PACKAGE_FILES:
            raise ValidationError(f"Pacote excede o limite de {MAX_PACKAGE_FILES} arquivos ({len(infolist)} encontrados).")

        for member in infolist:
            file_count += 1
            if file_count > MAX_PACKAGE_FILES:
                raise ValidationError(f"Pacote excede o limite de {MAX_PACKAGE_FILES} arquivos.")

            # Proteção contra Symlinks em ZIP (POSIX external_attr)
            # Bits 0o120000 indicam S_IFLNK
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValidationError(f"Links simbólicos (symlinks) são estritamente proibidos no pacote: {member.filename}")

            # Proteção contra ZipSlip / Path Traversal
            target_file = _sanitize_and_check_path(member.filename, dest_path)

            if member.is_dir() or member.filename.endswith('/'):
                target_file.mkdir(parents=True, exist_ok=True)
                os.chmod(target_file, 0o755)
                continue

            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Extração streaming com contagem real de bytes
            file_bytes_written = 0
            with zf.open(member) as src, open(target_file, "wb") as dst:
                while chunk := src.read(65536):
                    chunk_len = len(chunk)
                    file_bytes_written += chunk_len
                    total_uncompressed_bytes += chunk_len

                    if file_bytes_written > MAX_SINGLE_FILE_BYTES:
                        raise ValidationError(f"Arquivo individual excede o limite de {MAX_SINGLE_FILE_BYTES // (1024*1024)}MB: {member.filename}")
                    if total_uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                        raise ValidationError(f"Tamanho total descompactado excede o limite de {MAX_UNCOMPRESSED_BYTES // (1024*1024)}MB (ZipBomb mitigado).")

                    dst.write(chunk)

            # Enforça permissões seguras
            os.chmod(target_file, 0o644)

            rel_path = os.path.relpath(target_file, dest_path).replace("\\", "/")
            extracted_files.append({
                "file_path": rel_path,
                "file_size": file_bytes_written,
                "sha256": compute_sha256(str(target_file)),
                "is_critical": 1 if rel_path in ("Dockerfile", "docker-compose.yml", "compose.yaml", "manifest.yml", "manifest.yaml", "README.md") else 0
            })

    return extracted_files


def safe_extract_tar(archive_path: str | Path, extract_to: str | Path) -> list[dict]:
    """
    Extrai arquivo .tar / .tar.gz com mitigação contra:
    1. Path Traversal
    2. Symlinks e Hardlinks
    3. Device files, FIFOs e sockets
    4. Decompression bomb via streaming byte limit
    """
    validate_archive_magic_bytes(archive_path)

    dest_path = Path(extract_to).resolve()
    dest_path.mkdir(parents=True, exist_ok=True)

    extracted_files = []
    total_uncompressed_bytes = 0
    file_count = 0

    with tarfile.open(archive_path, 'r:*') as tf:
        for member in tf.getmembers():
            file_count += 1
            if file_count > MAX_PACKAGE_FILES:
                raise ValidationError(f"Pacote excede o limite de {MAX_PACKAGE_FILES} arquivos.")

            # Rejeição estrita de links simbólicos e hardlinks
            if member.issym() or member.islnk():
                raise ValidationError(f"Links simbólicos e hardlinks são proibidos no pacote: {member.name}")

            # Rejeição de arquivos de dispositivo e FIFOs
            if member.isdev() or member.ischr() or member.isblk() or member.isfifo():
                raise ValidationError(f"Dispositivos especiais e FIFOs não são permitidos: {member.name}")

            # Proteção contra Path Traversal
            target_file = _sanitize_and_check_path(member.name, dest_path)

            if member.isdir():
                target_file.mkdir(parents=True, exist_ok=True)
                os.chmod(target_file, 0o755)
                continue

            if not member.isreg():
                continue

            target_file.parent.mkdir(parents=True, exist_ok=True)

            src = tf.extractfile(member)
            if src is None:
                continue

            file_bytes_written = 0
            with src, open(target_file, "wb") as dst:
                while chunk := src.read(65536):
                    chunk_len = len(chunk)
                    file_bytes_written += chunk_len
                    total_uncompressed_bytes += chunk_len

                    if file_bytes_written > MAX_SINGLE_FILE_BYTES:
                        raise ValidationError(f"Arquivo individual excede o limite de {MAX_SINGLE_FILE_BYTES // (1024*1024)}MB: {member.name}")
                    if total_uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                        raise ValidationError(f"Tamanho total descompactado excede o limite de {MAX_UNCOMPRESSED_BYTES // (1024*1024)}MB (Decompression Bomb mitigado).")

                    dst.write(chunk)

            os.chmod(target_file, 0o644)

            rel_path = os.path.relpath(target_file, dest_path).replace("\\", "/")
            extracted_files.append({
                "file_path": rel_path,
                "file_size": file_bytes_written,
                "sha256": compute_sha256(str(target_file)),
                "is_critical": 1 if rel_path in ("Dockerfile", "docker-compose.yml", "compose.yaml", "manifest.yml", "manifest.yaml", "README.md") else 0
            })

    return extracted_files


def extract_package(archive_path: str | Path, extract_to: str | Path) -> list[dict]:
    """Extrai pacote conforme a extensão e validação de magic bytes."""
    kind = validate_archive_magic_bytes(archive_path)
    if kind == "zip":
        return safe_extract_zip(archive_path, extract_to)
    elif kind in ("tar", "tar.gz"):
        return safe_extract_tar(archive_path, extract_to)
    else:
        raise ValidationError("Formato de pacote não suportado. Envie um arquivo .zip ou .tar.gz legítimo.")


def validate_extracted_structure(extract_dir: str) -> dict:
    """
    Verifica se a estrutura mínima obrigatória existe e valida manifest.yml.
    Retorna o dicionário parseado do manifest.
    """
    base = Path(extract_dir)
    
    # 1. Verifica manifest.yml
    manifest_file = base / "manifest.yml"
    if not manifest_file.is_file():
        manifest_file = base / "manifest.yaml"
        if not manifest_file.is_file():
            raise ValidationError("Arquivo obrigatório 'manifest.yml' não encontrado na raiz do pacote.")

    # 2. Verifica Dockerfile ou docker-compose.yml
    has_dockerfile = (base / "Dockerfile").is_file()
    has_compose = (base / "docker-compose.yml").is_file() or (base / "compose.yaml").is_file()
    if not has_dockerfile and not has_compose:
        raise ValidationError("O pacote deve conter um 'Dockerfile' ou 'docker-compose.yml' na raiz.")

    # 3. Verifica README.md
    readme_file = base / "README.md"
    if not readme_file.is_file():
        raise ValidationError("Arquivo obrigatório 'README.md' não encontrado na raiz do pacote.")

    # 4. Parse do manifest
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
    except Exception as e:
        raise ValidationError(f"Erro de sintaxe no arquivo manifest.yml: {e}")

    if not isinstance(manifest, dict):
        raise ValidationError("O manifest.yml deve conter um objeto YAML válido na raiz.")

    # Valida seções obrigatórias
    for sec in REQUIRED_MANIFEST_SECTIONS:
        if sec not in manifest or not isinstance(manifest[sec], dict):
            raise ValidationError(f"Seção obrigatória '{sec}' ausente ou inválida no manifest.yml.")

    # Valida campos da seção machine
    m_info = manifest["machine"]
    if not m_info.get("name") or not isinstance(m_info["name"], str):
        raise ValidationError("Campo 'machine.name' é obrigatório no manifest.yml.")
    if not m_info.get("version"):
        manifest["machine"]["version"] = "1.0"

    # Valida metadata
    meta = manifest["metadata"]
    if not meta.get("os"):
        manifest["metadata"]["os"] = "linux"
    if not meta.get("difficulty"):
        manifest["metadata"]["difficulty"] = "medium"
    if not meta.get("category"):
        manifest["metadata"]["category"] = "web"

    return manifest
