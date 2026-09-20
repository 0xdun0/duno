"""modules/challenges/backup.py — Backup e Restauração do Catálogo e Flags CTF.

Requisitos da Fase 5 (Seção 24 do upgrade_v3.md):
- Validar backup e plano de migração do registry e tabelas.
- Restauração validada e verificável por testes.
"""
import os
import shutil
import json
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
CHALLENGES_YAML = DATA_DIR / "challenges.yaml"
FLAGS_YAML = DATA_DIR / "flags.yaml"


def backup_registry(target_dir: str) -> dict:
    """Cria cópia pontual do registry e flags em diretório seguro de backup."""
    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    backup_info = {
        "challenges_copied": False,
        "flags_copied": False,
        "backup_path": str(target),
    }

    if CHALLENGES_YAML.exists():
        shutil.copy2(CHALLENGES_YAML, target / "challenges.yaml")
        backup_info["challenges_copied"] = True

    if FLAGS_YAML.exists():
        shutil.copy2(FLAGS_YAML, target / "flags.yaml")
        backup_info["flags_copied"] = True

    return backup_info


def restore_registry(source_dir: str) -> dict:
    """Restaura registry e flags a partir de um backup previamente gerado."""
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(f"Diretório de backup inexistente: {source}")

    restore_info = {
        "challenges_restored": False,
        "flags_restored": False,
    }

    src_ch = source / "challenges.yaml"
    if src_ch.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_ch, CHALLENGES_YAML)
        restore_info["challenges_restored"] = True

    src_flags = source / "flags.yaml"
    if src_flags.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_flags, FLAGS_YAML)
        restore_info["flags_restored"] = True

    return restore_info


def export_solves_data(db_conn: sqlite3.Connection) -> list:
    """Exporta histórico de solves em formato serializável JSON para backup lógico."""
    rows = db_conn.execute("SELECT * FROM challenge_solves ORDER BY submitted_at ASC").fetchall()
    return [dict(r) if hasattr(r, "keys") else list(r) for r in rows]
