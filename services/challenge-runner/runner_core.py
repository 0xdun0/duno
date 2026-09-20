"""services/challenge-runner/runner_core.py — Núcleo de orquestração de containers do Challenge Runner."""
import os
import time
import uuid
import logging
import threading
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger("challenge_runner")

# Configurações padrão de limites e isolamento (Seção 19 e 21)
DEFAULT_TTL_SECONDS = int(os.environ.get("CHALLENGE_INSTANCE_TTL_SECONDS", 3600))
CPU_LIMIT = float(os.environ.get("CHALLENGE_CPU_LIMIT", 0.5))
MEMORY_LIMIT = os.environ.get("CHALLENGE_MEMORY_LIMIT", "512m")
PIDS_LIMIT = int(os.environ.get("CHALLENGE_PIDS_LIMIT", 100))
CHALLENGE_NETWORK = os.environ.get("CHALLENGE_NETWORK", "challenge-net")
EGRESS_ENABLED = os.environ.get("CHALLENGE_EGRESS_ENABLED", "false").lower() == "true"
CHALLENGE_SUBNET_PREFIX = os.environ.get("CHALLENGE_SUBNET_PREFIX", "10.10.15.")

CHALLENGES_ROOT = Path(os.environ.get("CHALLENGES_ROOT", "/opt/challenges"))

# Mapeamento estático e determinístico de IPs para a subnet de laboratório 10.10.15.0/24
CHALLENGE_IP_MAP = {
    "alpha-sqli-basics": "10.10.15.11",
    "bravo": "10.10.15.12",
    "charlie-cookie-tampering": "10.10.15.13",
    "cheerio": "10.10.15.14",
    "coffee": "10.10.15.15",
    "delta-idor-document-vault": "10.10.15.16",
    "echo-rate-limit-bypass": "10.10.15.17",
    "foxtrot-xss-support-tickets": "10.10.15.18",
    "golf-static-analysis-config": "10.10.15.19",
    "hotel-junior-dev-challenge": "10.10.15.20",
    "india-nosql-injection": "10.10.15.21",
    "juliet-xxe-injection": "10.10.15.22",
    "kilo-ssti-template-generator": "10.10.15.23",
    "lima-deserialization-session": "10.10.15.24",
    "mike-ssrf-to-rce": "10.10.15.25",
    "november-drupalgeddon": "10.10.15.26",
    "oscar-race-conditions": "10.10.15.27",
    "papa-graphql-injection": "10.10.15.28",
    "quebec-enumeration": "10.10.15.29",
    "romeo-dfir-memdump": "10.10.15.30",
    "sierra-filing-cabinet": "10.10.15.31",
    "tango-calculator": "10.10.15.32",
    "xray-craftcms-rce": "10.10.15.33",
    "yankee-log4shell": "10.10.15.34",
    "zulu-koa-devtools": "10.10.15.35",
}


def resolve_challenge_ip(challenge_id, challenge_meta=None):
    """Calcula o IP estático determinístico do desafio na subnet 10.10.15.0/24."""
    if challenge_id in CHALLENGE_IP_MAP:
        return CHALLENGE_IP_MAP[challenge_id]
    if challenge_meta and isinstance(challenge_meta, dict) and "target_ip" in challenge_meta:
        return challenge_meta["target_ip"]
    h = sum(ord(c) for c in challenge_id) % 200 + 40
    return f"{CHALLENGE_SUBNET_PREFIX}{h}"


def is_docker_available():
    try:
        res = subprocess.run(["docker", "ps"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
        return res.returncode == 0
    except Exception:
        return False


def resolve_docker_network(network_name):
    """Encontra o nome real da rede no docker daemon (com prefixo do compose se houver)."""
    try:
        res = subprocess.run(["docker", "network", "ls", "--format", "{{.Name}}"], stdout=subprocess.PIPE, text=True, timeout=5)
        nets = res.stdout.splitlines()
        if network_name in nets:
            return network_name
        for n in nets:
            if n.endswith(f"_{network_name}") or n == network_name:
                return n
    except Exception:
        pass
    return network_name


class ChallengeRunnerCore:
    """Gerencia instâncias ativas, ciclo de vida e comandos de container."""

    def __init__(self, dry_run=False):
        if dry_run or os.environ.get("RUNNER_DRY_RUN", "false").lower() == "true":
            self.dry_run = True
        else:
            self.dry_run = not is_docker_available()
        self._instances = {}
        self._lock = threading.Lock()
        self._failure_counts = {}  # challenge_id -> list of timestamps
        self._stop_cleanup_event = threading.Event()
        self._cleanup_thread = None

    def start_cleanup_worker(self, interval_seconds=15):
        """Inicia thread em background para purgar instâncias vencidas."""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        def worker():
            while not self._stop_cleanup_event.is_set():
                try:
                    self.cleanup_expired_instances()
                except Exception as e:
                    logger.error(f"Erro no cleanup worker: {e}")
                self._stop_cleanup_event.wait(interval_seconds)

        self._cleanup_thread = threading.Thread(target=worker, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_worker(self):
        self._stop_cleanup_event.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)

    def start_instance(self, instance_id, challenge_id, user_id, ttl_seconds=DEFAULT_TTL_SECONDS, challenge_meta=None):
        """
        Inicia uma instância isolada.
        Garante idempotência, limites de recursos, TTL e rede isolada.
        """
        with self._lock:
            if instance_id in self._instances:
                # Idempotência: já existe
                existing = self._instances[instance_id]
                return False, "Instance already exists", 409, existing

            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=ttl_seconds)

            container_name = f"duno-ctf-{challenge_id[:16]}-{instance_id[:8]}"
            port = challenge_meta.get("internal_port", 5000) if challenge_meta else 5000

            target_ip = resolve_challenge_ip(challenge_id, challenge_meta)
            instance_data: dict[str, Any] = {
                "instance_id": instance_id,
                "challenge_id": challenge_id,
                "user_id": user_id,
                "container_ref": container_name,
                "status": "starting",
                "endpoint": None,
                "target_ip": target_ip,
                "internal_port": port,
                "started_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "last_error": None,
            }
            self._instances[instance_id] = instance_data

        # Se for modo dry-run (testes sem daemon Docker)
        if self.dry_run:
            instance_data["status"] = "running"
            instance_data["endpoint"] = f"http://{target_ip}:{port}"
            return True, "Created", 201, instance_data

        # Modo Docker real
        try:
            success, endpoint, err = self._docker_run_instance(container_name, challenge_id, port, challenge_meta, target_ip=target_ip)
            with self._lock:
                if success:
                    instance_data["status"] = "running"
                    instance_data["endpoint"] = endpoint
                else:
                    instance_data["status"] = "failed"
                    instance_data["last_error"] = err or "Falha na inicialização do container"
                    self.record_build_failure(challenge_id)
            return True, "Created", 201, instance_data
        except Exception as e:
            with self._lock:
                instance_data["status"] = "failed"
                instance_data["last_error"] = "Erro interno no orquestrador"
                self.record_build_failure(challenge_id)
            return True, "Created", 201, instance_data

    def get_instance(self, instance_id):
        """Retorna o estado atual da instância ou None se não encontrada."""
        with self._lock:
            inst = self._instances.get(instance_id)
            if not inst:
                return None
            
            # Verifica expiração imediata
            expires_dt = datetime.fromisoformat(inst["expires_at"])
            if datetime.now(timezone.utc) > expires_dt and inst["status"] in ("starting", "running"):
                inst["status"] = "expired"
                self._stop_container(inst["container_ref"])
            return dict(inst)

    def stop_instance(self, instance_id):
        """Para e remove a instância de container."""
        with self._lock:
            inst = self._instances.get(instance_id)
            if not inst:
                return False, "Not found", 404

            if inst["status"] == "stopping":
                return False, "Instance is already stopping", 409

            inst["status"] = "stopping"
            container_ref = inst["container_ref"]

        # Executa remoção
        self._stop_container(container_ref)

        with self._lock:
            inst["status"] = "stopped"
            inst["endpoint"] = None

        return True, "Stopped", 204

    def extend_instance(self, instance_id, additional_seconds=3600):
        """Estende o tempo de expiração da instância ativa."""
        now = datetime.now(timezone.utc)
        with self._lock:
            inst = self._instances.get(instance_id)
            if not inst:
                return False, "Not found", 404
            if inst["status"] not in ("starting", "running"):
                return False, "Instance is not active", 400

            try:
                cur_exp = datetime.fromisoformat(str(inst["expires_at"]).replace("Z", "+00:00"))
            except Exception:
                cur_exp = now

            if cur_exp.tzinfo is None:
                cur_exp = cur_exp.replace(tzinfo=timezone.utc)

            base = max(cur_exp, now)
            new_exp = base + timedelta(seconds=additional_seconds)
            inst["expires_at"] = new_exp.isoformat()
            return True, inst["expires_at"], 200

    def cleanup_expired_instances(self):
        """Identifica e remove containers com TTL vencido."""
        now = datetime.now(timezone.utc)
        to_clean = []

        with self._lock:
            for iid, inst in self._instances.items():
                if inst["status"] in ("starting", "running"):
                    exp = datetime.fromisoformat(inst["expires_at"])
                    if now >= exp:
                        to_clean.append((iid, inst["container_ref"]))

        for iid, cref in to_clean:
            logger.info(f"Expirando instância {iid} (container: {cref})")
            self._stop_container(cref)
            with self._lock:
                if iid in self._instances:
                    self._instances[iid]["status"] = "expired"
                    self._instances[iid]["endpoint"] = None

    def record_build_failure(self, challenge_id):
        """Registra falha de build e aciona maintenance se >= 3 falhas em 24h."""
        now = time.time()
        window = 86400  # 24h
        with self._lock:
            timestamps = self._failure_counts.setdefault(challenge_id, [])
            timestamps.append(now)
            # Filtra apenas falhas das últimas 24h
            recent = [t for t in timestamps if now - t <= window]
            self._failure_counts[challenge_id] = recent
            if len(recent) >= 3:
                logger.warning(f"Desafio {challenge_id} atingiu {len(recent)} falhas consecutivas! Movendo para maintenance.")
                return True
        return False

    def get_failure_count(self, challenge_id):
        with self._lock:
            now = time.time()
            return len([t for t in self._failure_counts.get(challenge_id, []) if now - t <= 86400])

    def _docker_run_instance(self, container_name, challenge_id, port, challenge_meta, target_ip=None):
        """Executa docker build e run aplicando limites rigorosos e IP estático na rede challenge-net."""
        if not target_ip:
            target_ip = resolve_challenge_ip(challenge_id, challenge_meta)

        # Caminho da pasta do desafio
        src_path = challenge_meta.get("source_path") if challenge_meta else f"challenges/{challenge_id}"
        challenge_dir = (CHALLENGES_ROOT / Path(src_path).name).resolve()
        if not challenge_dir.exists():
            challenge_dir = (Path.cwd() / src_path).resolve()

        if not challenge_dir.exists():
            return False, None, f"Pasta do desafio não encontrada: {src_path}"

        image_tag = f"duno-img-{challenge_id}:latest"

        # 1. Build da imagem (apenas se não existir)
        res_img = subprocess.run(["docker", "image", "inspect", image_tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
        if res_img.returncode != 0:
            print(f"[runner] Building image {image_tag} from {challenge_dir}...", flush=True)
            build_cmd = ["docker", "build", "-t", image_tag, str(challenge_dir)]
            res_b = subprocess.run(build_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=180)
            if res_b.returncode != 0:
                print(f"[runner] Build failed: {res_b.stderr}", flush=True)
                return False, None, "Falha na compilação da imagem Docker."
        else:
            print(f"[runner] Image {image_tag} already exists, skipping build.", flush=True)

        # 2. Run do container com IP estático 10.10.15.xx e porta mapeada no host
        net_name = resolve_docker_network(CHALLENGE_NETWORK)
        print(f"[runner] Starting container {container_name} on network {net_name} IP {target_ip} port {port}...", flush=True)
        run_cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"0.0.0.0:0:{port}",
            "--network", net_name,
            "--ip", target_ip,
            "--memory", MEMORY_LIMIT,
            "--cpus", str(CPU_LIMIT),
            "--pids-limit", str(PIDS_LIMIT),
            "--rm",
            image_tag,
        ]
        res_r = subprocess.run(run_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
        if res_r.returncode != 0:
            err_msg = res_r.stderr.strip() if res_r.stderr else "Falha na execução do container Docker."
            print(f"[runner] Container run failed: {err_msg}", flush=True)
            return False, None, err_msg

        print(f"[runner] Container {container_name} started: {res_r.stdout.strip()}", flush=True)

        # O endpoint primário da arquitetura CTF é o IP direto da subnet 10.10.15.0/24
        endpoint = f"http://{target_ip}:{port}"
        return True, endpoint, None

    def _stop_container(self, container_ref):
        if self.dry_run or not container_ref:
            return
        try:
            subprocess.run(["docker", "stop", "-t", "2", container_ref], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            pass
