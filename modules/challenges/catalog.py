"""modules/challenges/catalog.py — Catálogo e registro de Desafios CTF do DUNO."""
import os
import re
import yaml
from pathlib import Path

VALID_DIFFICULTIES = ("easy", "medium", "hard", "insane")
VALID_ENVIRONMENTS = ("single", "compose", "external")
VALID_STATUSES = ("draft", "available", "maintenance", "disabled")
VALID_PROTOCOLS = ("http", "https", "tcp", "mixed")
SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def get_registry_path():
    """Retorna o caminho do arquivo de catálogo de desafios."""
    custom = os.environ.get("CHALLENGES_REGISTRY")
    if custom and os.path.isfile(custom):
        return Path(custom)
    
    # Busca local ou no container
    base_dir = Path(__file__).resolve().parent.parent.parent
    try:
        from flask_babel import get_locale
        locale = str(get_locale())
        if locale and locale != 'pt':
            cand = base_dir / "data" / f"challenges_{locale}.yaml"
            if cand.is_file():
                return cand
    except Exception:
        pass

    candidates = [
        base_dir / "data" / "challenges.yaml",
        Path("/app/data/challenges.yaml"),
        Path("data/challenges.yaml"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return candidates[0]


CHALLENGE_CARD_DESCRIPTIONS = {
    "alpha-sqli-basics": "Analise o ambiente, identifique as vulnerabilidades presentes e obtenha acesso à flag final.",
    "bravo": "Explore a superfície de ataque da aplicação, investigue os fluxos de autenticação e capture as flags.",
    "charlie-cookie-tampering": "Analise a persistência de sessão, contorne as restrições de acesso e localize os dados confidenciais.",
    "cheerio": "Audite os parâmetros da aplicação web, teste os vetores de entrada e obtenha acesso elevado.",
    "coffee": "Investigue o serviço em execução, descubra pontos cegos na arquitetura e extraia a flag final.",
    "delta-idor-document-vault": "Mapeie os endpoints do sistema de arquivos, contorne o controle de permissões e colete os artefatos.",
    "echo-rate-limit-bypass": "Avalie a resiliência das rotas contra requisições anômalas, explore falhas lógicas e capture a flag.",
    "foxtrot-xss-support-tickets": "Examine os pontos de interação da aplicação, rastreie o comportamento de usuários e eleve privilégios.",
    "golf-static-analysis-config": "Audite os artefatos disponíveis, localize chaves e configurações expostas e comprometa o servidor.",
    "hotel-junior-dev-challenge": "Inspecione os recursos da aplicação, teste os mecanismos de controle e execute a invasão do alvo.",
    "india-nosql-injection": "Identifique anomalias no processamento de consultas, explore falhas de validação e acesse o banco.",
    "juliet-xxe-injection": "Mapeie a ingestão de dados da API, force o vazamento de arquivos internos e domine o sistema.",
    "kilo-ssti-template-generator": "Investigue o mecanismo de renderização do backend, explore a injeção de comandos e obtenha acesso root.",
    "lima-deserialization-session": "Audite o tráfego serializado, quebre as restrições da sessão corporativa e comprometa a máquina.",
    "mike-ssrf-to-rce": "Descubra serviços internos protegidos pelo perímetro, abuse de requisições do servidor e capture a flag.",
    "november-drupalgeddon": "Identifique serviços desatualizados no alvo, explore vetores conhecidos de RCE e obtenha acesso privilegiado.",
    "oscar-race-conditions": "Analise concorrência de operações sensíveis, explore janelas temporais críticas e obtenha a recompensa.",
    "papa-graphql-injection": "Investigue a API exposta, mapeie o esquema de consultas ocultas e extraia as informações restritas.",
    "quebec-enumeration": "Realize reconhecimento exaustivo no servidor, descubra ativos ocultos e localize todas as evidências.",
    "romeo-dfir-memdump": "Analise artefatos de memória volátil, investigue rastros de incidentes e recupere as chaves criptográficas.",
    "sierra-filing-cabinet": "Explore as permissões do sistema de arquivos compartilhado, localize diretórios sensíveis e capture a flag.",
    "tango-calculator": "Analise as rotinas de cálculo do backend, explore falhas de interpretação de código e assuma o controle.",
    "xray-craftcms-rce": "Mapeie o painel administrativo, identifique vulnerabilidades no gerenciamento de ativos e execute comandos.",
    "yankee-log4shell": "Identifique vetores de registro vulneráveis, explore a execução remota de código e obtenha o shell.",
    "zulu-koa-devtools": "Analise ferramentas de desenvolvimento ativas em produção, descubra falhas de debug e capture a flag final.",
}

CHALLENGE_FLAGS_INFO = {
    "alpha-sqli-basics": "5 Flags + Root",
    "bravo": "3 Flags + Root",
    "charlie-cookie-tampering": "2 Flags + Root",
    "cheerio": "2 Flags + Root",
    "coffee": "2 Flags + Root",
    "delta-idor-document-vault": "4 Flags + Root",
    "echo-rate-limit-bypass": "2 Flags + Root",
    "foxtrot-xss-support-tickets": "3 Flags + Root",
    "golf-static-analysis-config": "5 Flags + Root",
    "hotel-junior-dev-challenge": "2 Flags + Root",
    "india-nosql-injection": "3 Flags + Root",
    "juliet-xxe-injection": "5 Flags + Root",
    "kilo-ssti-template-generator": "2 Flags + Root",
    "lima-deserialization-session": "2 Flags + Root",
    "mike-ssrf-to-rce": "3 Flags + Root",
    "november-drupalgeddon": "3 Flags + Root",
    "oscar-race-conditions": "2 Flags + Root",
    "papa-graphql-injection": "2 Flags + Root",
    "quebec-enumeration": "15 Flags + Root",
    "romeo-dfir-memdump": "3 Flags + Root",
    "sierra-filing-cabinet": "2 Flags + Root",
    "tango-calculator": "2 Flags + Root",
    "xray-craftcms-rce": "2 Flags + Root",
    "yankee-log4shell": "2 Flags + Root",
    "zulu-koa-devtools": "2 Flags + Root",
}


def _challenges_base_dir() -> Path:
    """Diretório raiz das challenges (mesma resolução usada pelo runner)."""
    return Path(__file__).resolve().parent.parent.parent / "challenges"


def _challenge_has_walkthrough(challenge_id: str) -> bool:
    """True se a challenge possui walkthrough.md (convenção p/ View Walkthrough)."""
    return get_challenge_walkthrough_path(challenge_id) is not None


def get_challenge_walkthrough_path(challenge: dict):
    """Retorna o Path do walkthrough.md da challenge, ou None se não existir."""
    try:
        source = challenge.get("source_path")
        if not source:
            source = f"challenges/{challenge.get('id')}"
            
        base = Path(__file__).resolve().parent.parent.parent
        cdir = base / source
        for cand in (cdir / "walkthrough.md", cdir / "WALKTHROUGH.md"):
            if cand.is_file():
                return cand
    except Exception:
        pass
    return None


class ChallengeCatalog:
    """Gerenciador do catálogo de desafios em memória e integração com DB."""
    def __init__(self, registry_path=None):
        self.registry_path = Path(registry_path) if registry_path else get_registry_path()
        self._cache = None
        self._last_mtime: float = 0.0

    def load_challenges(self, force_reload=False):
        """Carrega e valida os desafios a partir do YAML e do banco de dados (máquinas publicadas)."""
        current_path = get_registry_path()
        mtime: float = 0.0
        if not current_path.exists():
            base_data = []
        else:
            try:
                mtime = float(current_path.stat().st_mtime)
            except Exception:
                mtime = 0.0

            # O cache deve levar em conta o path para não servir cache em idioma errado
            cache_key = str(current_path)
            if not getattr(self, '_cache_by_path', None):
                self._cache_by_path = {}
                
            cached_data = self._cache_by_path.get(cache_key)
            if not force_reload and cached_data is not None and mtime == cached_data.get('mtime'):
                return cached_data.get('data')

            try:
                with open(current_path, "r", encoding="utf-8") as f:
                    import yaml
                    raw = yaml.safe_load(f)
                    base_data = raw if isinstance(raw, list) else []
            except Exception as e:
                import logging
                logging.error(f"Erro ao carregar registry de desafios: {e}")
                base_data = []

        validated = []
        for item in base_data:
            if not isinstance(item, dict):
                continue
            validated.append(self._normalize_challenge(item))

        # Inclusão dinâmica de máquinas aprovadas e publicadas pela comunidade
        try:
            from core.database import get_db
            import json
            db = get_db()
            pub_rows = db.execute("""
                SELECT p.challenge_id, p.published_version, p.published_at,
                       s.id as submission_id, s.name, s.slug, s.user_id as author_id,
                       u.username as author_username,
                       m.short_desc, m.full_desc, m.os_type, m.author_difficulty,
                       m.category, m.exposed_ports_json, m.hints_json, m.objectives_json,
                       m.cpu_limit, m.memory_limit_mb
                FROM published_machines p
                JOIN machine_submissions s ON s.id = p.submission_id
                LEFT JOIN users u ON u.id = s.user_id
                JOIN machine_versions v ON v.submission_id = s.id AND v.version_str = p.published_version
                LEFT JOIN machine_metadata m ON m.version_id = v.id
                WHERE p.is_active = 1
                ORDER BY p.published_at ASC
            """).fetchall()

            for prow in pub_rows:
                cid = prow["challenge_id"]
                if any(x["id"] == cid for x in validated):
                    continue

                flags_rows = db.execute(
                    "SELECT flag_type FROM machine_flags WHERE submission_id = ?",
                    (prow["submission_id"],)
                ).fetchall()
                flag_count = len(flags_rows)
                calc_points = flag_count * 100 if flag_count > 0 else 150
                flags_info = f"{flag_count} Flags + Root" if flag_count > 0 else "2 Flags + Root"

                exposed_ports = []
                try:
                    if prow["exposed_ports_json"]:
                        exposed_ports = json.loads(prow["exposed_ports_json"])
                except Exception:
                    pass
                internal_port = int(exposed_ports[0]) if exposed_ports else 80

                pub_item = {
                    "id": cid,
                    "source": "community",
                    "source_path": f"challenges/{cid}",
                    "category": prow["category"] or "Web",
                    "name": prow["name"],
                    "short_description": prow["short_desc"] or f"Máquina {prow['name']} da comunidade.",
                    "long_description": prow["full_desc"] or prow["short_desc"] or "",
                    "card_description": prow["short_desc"] or "Analise o ambiente, identifique as vulnerabilidades presentes e capture as flags.",
                    "flags_info": flags_info,
                    "difficulty": (prow["author_difficulty"] or "medium").lower(),
                    "points": calc_points,
                    "estimated_minutes": 45,
                    "solves_count": 0,
                    "environment_type": "single",
                    "internal_port": internal_port,
                    "protocol": "http",
                    "os": (prow["os_type"] or "linux").lower(),
                    "status": "available",
                    "objective": prow["short_desc"] or "",
                    "instructions": "Conecte-se ao IP do alvo na rede CTF e explore o ambiente vulnerável.",
                    "hints": json.loads(prow["hints_json"]) if prow["hints_json"] else [],
                    "requires_api_key": False,
                    "has_walkthrough": _challenge_has_walkthrough(cid),
                    "metadata_version": 1,
                    "is_community": True,
                    "author": prow["author_username"] or "Comunidade",
                    "published_at": (prow["published_at"].isoformat() if hasattr(prow["published_at"], "isoformat") else str(prow["published_at"])) if prow["published_at"] is not None else None,
                }
                validated.append(self._normalize_challenge(pub_item))
        except Exception:
            pass

        self._cache = validated
        self._last_mtime = mtime
        
        # O novo cache baseado em path
        if hasattr(self, '_cache_by_path'):
            self._cache_by_path[str(get_registry_path())] = {'mtime': mtime, 'data': validated}
            
        return validated

    def _normalize_challenge(self, item):
        """Assegura tipos e campos obrigatórios com valores padrão seguros."""
        cid = str(item.get("id", "")).strip()
        card_desc = item.get("card_description") or CHALLENGE_CARD_DESCRIPTIONS.get(
            cid, "Analise o ambiente, identifique as vulnerabilidades presentes e obtenha acesso à flag final."
        )
        flags_info = CHALLENGE_FLAGS_INFO.get(cid, item.get("flags_info") or "2 Flags + Root")

        return {
            "id": cid,
            "source": str(item.get("source", "eversec")),
            "source_path": str(item.get("source_path", "")),
            "category": str(item.get("category", "Geral")),
            "name": str(item.get("name", item.get("id", ""))),
            "short_description": str(item.get("short_description", "")),
            "long_description": str(item.get("long_description", "")),
            "card_description": card_desc,
            "flags_info": flags_info,
            "difficulty": str(item.get("difficulty", "medium")).lower(),
            "points": int(item.get("points", 100)),
            "estimated_minutes": int(item.get("estimated_minutes", 30)),
            "solves_count": int(item.get("solves_count", 0)),
            "environment_type": str(item.get("environment_type", "single")).lower(),
            "internal_port": int(item["internal_port"]) if item.get("internal_port") else None,
            "protocol": str(item.get("protocol", "http")).lower(),
            "os": str(item.get("os", "linux")).lower(),
            "status": str(item.get("status", "available")).lower(),
            "objective": str(item.get("objective", "")),
            "instructions": str(item.get("instructions", "")),
            "hints": list(item.get("hints", [])),
            "requires_api_key": bool(item.get("requires_api_key", False)),
            "has_walkthrough": bool(item.get("has_walkthrough", False)),
            "metadata_version": int(item.get("metadata_version", 1)),
            "is_community": bool(item.get("is_community", False)),
            "author": str(item.get("author", "DUNO")),
            "published_at": (item["published_at"].isoformat() if hasattr(item.get("published_at"), "isoformat") else str(item["published_at"])) if item.get("published_at") is not None else None,
            "is_new": bool(item.get("is_new", False)),
        }

    def list_available_for_user(self, user=None):
        """Lista desafios disponíveis, anotando estado de instância e solve se houver usuário."""
        challenges = [c for c in self.load_challenges(force_reload=True) if c["status"] != "draft"]
        if not user:
            return challenges

        user_id = user["id"] if isinstance(user, dict) else user
        solves = set()
        active_instances = {}
        viewed_challenges = set()

        solves_counts = {}
        try:
            from core.database import get_db
            db = get_db()
            # Busca solves do usuário
            rows_s = db.execute(
                "SELECT challenge_id FROM challenge_solves WHERE user_id=?", (user_id,)
            ).fetchall()
            solves = {r["challenge_id"] for r in rows_s}

            # Busca visualizações para calcular is_new
            rows_v = db.execute(
                "SELECT challenge_id FROM user_challenge_views WHERE user_id=?", (user_id,)
            ).fetchall()
            viewed_challenges = {r["challenge_id"] for r in rows_v}

            # Contagem total de solves por desafio
            rows_cnt = db.execute(
                "SELECT challenge_id, COUNT(DISTINCT user_id) as cnt FROM challenge_solves GROUP BY challenge_id"
            ).fetchall()
            for r in rows_cnt:
                solves_counts[r["challenge_id"]] = r["cnt"]

            # Busca instâncias ativas
            rows_i = db.execute(
                """SELECT challenge_id, id, status, endpoint, expires_at
                   FROM challenge_instances
                   WHERE user_id=? AND status IN ('starting', 'running')""",
                (user_id,),
            ).fetchall()
            for r in rows_i:
                active_instances[r["challenge_id"]] = dict(r)
        except Exception:
            # Caso as tabelas ainda não existam ou DB em transição
            pass

        enriched = []
        for c in challenges:
            item = dict(c)
            item["is_solved"] = item["id"] in solves
            item["solves_count"] = item.get("solves_count", 0) + solves_counts.get(item["id"], 0)
            
            # Badge NOVA MÁQUINA para alvos da comunidade que o usuário ainda não abriu
            is_new = False
            if item.get("is_community") or item.get("published_at"):
                if user:
                    is_new = (item["id"] not in viewed_challenges)
                else:
                    is_new = True
            item["is_new"] = is_new

            inst = active_instances.get(item["id"])
            if inst:
                item["instance_id"] = inst["id"]
                item["instance_status"] = inst["status"]
                item["endpoint"] = inst.get("endpoint")
                item["expires_at"] = inst.get("expires_at")
            else:
                item["instance_status"] = "available" if item["status"] == "available" else item["status"]
                item["endpoint"] = None
                item["expires_at"] = None
            enriched.append(item)

        return enriched

    def get_by_id(self, challenge_id):
        """Busca um desafio por ID validado via allowlist do catálogo."""
        if not challenge_id or not SLUG_REGEX.match(challenge_id):
            return None
        for c in self.load_challenges():
            if c["id"] == challenge_id:
                item = dict(c)
                try:
                    from core.database import get_db
                    db = get_db()
                    row = db.execute(
                        "SELECT COUNT(DISTINCT user_id) as cnt FROM challenge_solves WHERE challenge_id=?",
                        (challenge_id,),
                    ).fetchone()
                    if row:
                        item["solves_count"] = item.get("solves_count", 0) + int(row["cnt"])
                except Exception:
                    pass
                return item
        return None

    def get_by_identifier(self, identifier, user=None):
        """Busca desafio por índice numérico (1, 2, 3) ou slug ID, enriquecendo com dados de usuário."""
        if not identifier:
            return None, None

        challenges = self.load_challenges()
        target_challenge = None
        target_index = None

        id_str = str(identifier).strip()
        if id_str.isdigit():
            idx = int(id_str)
            if 1 <= idx <= len(challenges):
                target_challenge = challenges[idx - 1]
                target_index = idx
        else:
            for i, c in enumerate(challenges, start=1):
                if c["id"] == id_str:
                    target_challenge = c
                    target_index = i
                    break

        if not target_challenge:
            return None, None

        item = dict(target_challenge)
        user_id = user["id"] if isinstance(user, dict) else user
        if user_id:
            try:
                from core.database import get_db
                db = get_db()
                row_solve = db.execute(
                    "SELECT 1 FROM challenge_solves WHERE user_id=? AND challenge_id=?",
                    (user_id, item["id"]),
                ).fetchone()
                item["is_solved"] = bool(row_solve)

                row_cnt = db.execute(
                    "SELECT COUNT(DISTINCT user_id) as cnt FROM challenge_solves WHERE challenge_id=?",
                    (item["id"],),
                ).fetchone()
                if row_cnt:
                    item["solves_count"] = item.get("solves_count", 0) + int(row_cnt["cnt"])

                row_inst = db.execute(
                    """SELECT id, status, endpoint, expires_at
                       FROM challenge_instances
                       WHERE user_id=? AND challenge_id=? AND status IN ('starting', 'running')
                       ORDER BY id DESC LIMIT 1""",
                    (user_id, item["id"]),
                ).fetchone()
                if row_inst:
                    inst_dict = dict(row_inst)
                    item["instance_id"] = inst_dict["id"]
                    item["instance_status"] = inst_dict["status"]
                    item["endpoint"] = inst_dict.get("endpoint")
                    item["expires_at"] = inst_dict.get("expires_at")
                else:
                    item["instance_status"] = "available" if item["status"] == "available" else item["status"]
                    item["endpoint"] = None
                    item["expires_at"] = None
            except Exception:
                pass

        return item, target_index


# Instância singleton padrão do catálogo
catalog = ChallengeCatalog()
