"""core/docs_manager.py — Gerenciador de Documentação Técnica do DUNO.
Carrega, cataloga, converte Markdown para HTML e fornece índice de busca dinâmico.
"""
import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import markdown

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

def _load_docs_data():
    try:
        from flask_babel import get_locale
        locale = str(get_locale())
    except Exception:
        locale = "pt"
    
    yaml_path = DATA_DIR / f"docs_{locale}.yaml"
    if not yaml_path.exists():
        yaml_path = DATA_DIR / "docs_base.yaml"
        
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception:
        # Fallback de emergência
        with open(DATA_DIR / "docs_base.yaml", 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

def get_all_categories() -> List[Dict[str, Any]]:
    """Retorna lista de categorias com os metadados dos seus documentos."""
    data = _load_docs_data()
    categories = data.get('categories', [])
    docs_metadata = data.get('metadata', {})
    
    res = []
    for cat in categories:
        cat_copy = dict(cat)
        cat_docs = []
        for slug in cat.get("docs", []):
            if slug in docs_metadata:
                meta = dict(docs_metadata[slug])
                meta["slug"] = slug
                cat_docs.append(meta)
        cat_copy["articles"] = cat_docs
        cat_copy["count"] = len(cat_docs)
        res.append(cat_copy)
    return res


def get_doc_metadata(slug: str) -> Optional[Dict[str, Any]]:
    """Recupera metadados de um documento pelo slug."""
    data = _load_docs_data()
    docs_metadata = data.get('metadata', {})
    if slug not in docs_metadata:
        return None
    meta = dict(docs_metadata[slug])
    meta["slug"] = slug
    return meta


def get_doc_content(slug: str) -> Optional[Dict[str, Any]]:
    """Lê o arquivo Markdown, converte para HTML e extrai cabeçalhos para o Sumário."""
    meta = get_doc_metadata(slug)
    if not meta:
        return None

    filepath = DOCS_DIR / meta["file"]
    if not filepath.is_file():
        # Tenta fallback para arquivo minúsculo
        filepath = DOCS_DIR / meta["file"].lower()
        if not filepath.is_file():
            return None

    raw_text = filepath.read_text(encoding="utf-8")

    # Extrai Table of Contents (H2 e H3)
    toc = []
    for line in raw_text.splitlines():
        h2_match = re.match(r"^##\s+(.+)$", line)
        h3_match = re.match(r"^###\s+(.+)$", line)
        if h2_match:
            title = h2_match.group(1).strip()
            anchor = re.sub(r"[^\w\- ]", "", title).strip().lower().replace(" ", "-")
            toc.append({"level": 2, "title": title, "anchor": anchor})
        elif h3_match:
            title = h3_match.group(1).strip()
            anchor = re.sub(r"[^\w\- ]", "", title).strip().lower().replace(" ", "-")
            toc.append({"level": 3, "title": title, "anchor": anchor})

    md = markdown.Markdown(extensions=["fenced_code", "tables", "attr_list", "sane_lists"])
    html_content = md.convert(raw_text)

    def add_header_ids(match):
        tag = match.group(1)
        text = match.group(2)
        clean_text = re.sub(r"<[^>]+>", "", text)
        anchor = re.sub(r"[^\w\- ]", "", clean_text).strip().lower().replace(" ", "-")
        return f'<{tag} id="{anchor}">{text}</{tag}>'

    html_content = re.sub(r"<(h[23])>(.*?)</\1>", add_header_ids, html_content)

    data = _load_docs_data()
    categories = data.get('categories', [])
    docs_metadata = data.get('metadata', {})
    
    all_slugs = []
    for cat in categories:
        all_slugs.extend(cat.get("docs", []))

    current_idx = all_slugs.index(slug) if slug in all_slugs else -1
    prev_doc = docs_metadata[all_slugs[current_idx - 1]] if current_idx > 0 else None
    if prev_doc:
        prev_doc = dict(prev_doc)
        prev_doc["slug"] = all_slugs[current_idx - 1]

    next_doc = docs_metadata[all_slugs[current_idx + 1]] if current_idx >= 0 and current_idx < len(all_slugs) - 1 else None
    if next_doc:
        next_doc = dict(next_doc)
        next_doc["slug"] = all_slugs[current_idx + 1]

    return {
        "metadata": meta,
        "toc": toc,
        "html_content": html_content,
        "raw_text": raw_text,
        "prev_doc": prev_doc,
        "next_doc": next_doc
    }


def search_docs(query: str) -> List[Dict[str, Any]]:
    """Busca em títulos, descrições, tags e texto dos documentos."""
    if not query or not query.strip():
        return []

    q = query.strip().lower()
    results = []
    
    data = _load_docs_data()
    docs_metadata = data.get('metadata', {})

    for slug, meta in docs_metadata.items():
        score = 0
        title_lower = meta["title"].lower()
        desc_lower = meta["desc"].lower()
        tag_lower = meta.get("tag", "").lower()

        if q == slug:
            score += 100
        if q in title_lower:
            score += 50
        if q in tag_lower:
            score += 30
        if q in desc_lower:
            score += 20

        filepath = DOCS_DIR / meta["file"]
        snippet = ""
        if filepath.is_file():
            content = filepath.read_text(encoding="utf-8")
            content_lower = content.lower()
            if q in content_lower:
                score += 10
                pos = content_lower.find(q)
                start = max(0, pos - 60)
                end = min(len(content), pos + 120)
                snippet = "..." + content[start:end].replace("\n", " ").strip() + "..."

        if score > 0:
            item = dict(meta)
            item["slug"] = slug
            item["score"] = score
            item["snippet"] = snippet or meta["desc"]
            results.append(item)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:10]

def get_whats_new():
    return _load_docs_data().get('timeline', [])

def get_search_suggestions():
    return _load_docs_data().get('search', [])
