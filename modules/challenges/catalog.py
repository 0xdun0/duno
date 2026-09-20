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


class ChallengeCatalog:
    """Gerenciador do catálogo de desafios em memória e integração com DB."""

    def __init__(self, registry_path=None):
        self.registry_path = Path(registry_path) if registry_path else get_registry_path()
        self._cache = None
        self._last_mtime = 0

    def load_challenges(self, force_reload=False):
        """Carrega e valida os desafios a partir do YAML."""
        if not self.registry_path.exists():
            return []

        try:
            mtime = self.registry_path.stat().st_mtime
        except Exception:
            mtime = 0

        if not force_reload and self._cache is not None and mtime == self._last_mtime:
            return self._cache

        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or []

        validated = []
        for item in data:
            if not isinstance(item, dict):
                continue
            validated.append(self._normalize_challenge(item))

        self._cache = validated
        self._last_mtime = mtime
        return self._cache

    def _normalize_challenge(self, item):
        """Assegura tipos e campos obrigatórios com valores padrão seguros."""
        cid = str(item.get("id", "")).strip()
        card_desc = CHALLENGE_CARD_DESCRIPTIONS.get(
            cid, "Analise o ambiente, identifique as vulnerabilidades presentes e obtenha acesso à flag final."
        )
        flags_info = CHALLENGE_FLAGS_INFO.get(cid, "2 Flags + Root")

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
        }

    def list_available_for_user(self, user=None):
        """Lista desafios disponíveis, anotando estado de instância e solve se houver usuário."""
        challenges = [c for c in self.load_challenges() if c["status"] != "draft"]
        if not user:
            return challenges

        user_id = user["id"] if isinstance(user, dict) else user
        solves = set()
        active_instances = {}

        solves_counts = {}
        try:
            from core.database import get_db
            db = get_db()
            # Busca solves do usuário
            rows_s = db.execute(
                "SELECT challenge_id FROM challenge_solves WHERE user_id=?", (user_id,)
            ).fetchall()
            solves = {r["challenge_id"] for r in rows_s}

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
