"""services/challenge-runner/app.py — Servidor HTTP do Challenge Runner."""
import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, abort

# Adiciona diretório local e raiz ao path
LOCAL_DIR = Path(__file__).resolve().parent
if str(LOCAL_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_DIR))

BASE_DIR = LOCAL_DIR.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from runner_core import ChallengeRunnerCore
except ImportError:
    from services.challenge_runner.runner_core import ChallengeRunnerCore

RUNNER_TOKEN = os.environ.get("CHALLENGE_RUNNER_TOKEN", "duno-runner-secret-key")
RUNNER_PORT = int(os.environ.get("CHALLENGE_RUNNER_PORT", 9000))

app = Flask(__name__)
runner: ChallengeRunnerCore = ChallengeRunnerCore()
if not os.environ.get("TESTING"):
    runner.start_cleanup_worker(interval_seconds=15)


def check_auth():
    """Valida o header X-Runner-Token contra a chave secreta compartilhada."""
    token = request.headers.get("X-Runner-Token")
    print(f"[runner-auth] Received token: {token!r} (expected: {RUNNER_TOKEN!r})", flush=True)
    if not token or token != RUNNER_TOKEN:
        abort(401, description="Unauthorized: Invalid or missing X-Runner-Token")


@app.route("/healthz", methods=["GET"])
def healthz():
    """Healthcheck endpoint (público dentro da rede interna)."""
    return jsonify({"status": "ok"}), 200


@app.route("/instances", methods=["POST"])
def create_instance():
    """Inicia uma instância isolada sob demanda."""
    print("[runner] POST /instances called", flush=True)
    check_auth()
    data = request.get_json(silent=True)
    print(f"[runner] POST /instances payload: {data}", flush=True)
    if not data:
        return jsonify({"error": "Bad Request: JSON body required"}), 400

    instance_id = data.get("instance_id")
    challenge_id = data.get("challenge_id")
    user_id = data.get("user_id")
    ttl_seconds = data.get("ttl_seconds", 3600)
    challenge_meta = data.get("challenge_meta")

    if not instance_id or not challenge_id or not user_id:
        return jsonify({"error": "Missing required fields (instance_id, challenge_id, user_id)"}), 400

    print(f"[runner] calling runner.start_instance for {challenge_id}...", flush=True)
    ok, msg, code, inst = runner.start_instance(
        instance_id=instance_id,
        challenge_id=challenge_id,
        user_id=user_id,
        ttl_seconds=ttl_seconds,
        challenge_meta=challenge_meta,
    )
    print(f"[runner] runner.start_instance finished: {ok}, {msg}, {code}, {inst}", flush=True)

    if not ok and code == 409:
        return jsonify({
            "error": msg,
            "instance_id": inst["instance_id"],
            "status": inst["status"],
            "endpoint": inst.get("endpoint"),
            "expires_at": inst.get("expires_at"),
        }), 409

    return jsonify({
        "instance_id": inst["instance_id"],
        "status": inst["status"],
        "endpoint": inst.get("endpoint"),
        "expires_at": inst["expires_at"],
        "last_error": inst.get("last_error"),
    }), code


@app.route("/instances/<instance_id>", methods=["GET"])
def get_instance_status(instance_id):
    """Consulta o status de uma instância."""
    check_auth()
    inst = runner.get_instance(instance_id)
    if not inst:
        return jsonify({"error": "Instance not found"}), 404

    return jsonify({
        "instance_id": inst["instance_id"],
        "challenge_id": inst["challenge_id"],
        "status": inst["status"],
        "endpoint": inst.get("endpoint"),
        "expires_at": inst["expires_at"],
        "last_error": inst.get("last_error"),
    }), 200


@app.route("/instances/<instance_id>", methods=["DELETE"])
def stop_instance(instance_id):
    """Para e purga a instância."""
    check_auth()
    ok, msg, code = runner.stop_instance(instance_id)
    if not ok:
        return jsonify({"error": msg}), code

    return "", 204


@app.route("/instances/<instance_id>/extend", methods=["POST"])
def extend_instance(instance_id):
    """Estende o TTL da instância ativa."""
    check_auth()
    data = request.get_json(silent=True) or {}
    additional_seconds = data.get("additional_seconds", 3600)
    ok, exp, code = runner.extend_instance(instance_id, additional_seconds=additional_seconds)
    if not ok:
        return jsonify({"error": exp}), code
    return jsonify({"instance_id": instance_id, "expires_at": exp}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=RUNNER_PORT)
