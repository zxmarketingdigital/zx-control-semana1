#!/usr/bin/env python3
"""
Instala e configura a Evolution API localmente para a Operacao IA.
"""

import json
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
EVOLUTION_DIR = BASE_DIR / "evolution-api"
ENV_PATH = EVOLUTION_DIR / ".env"
COMPOSE_PATH = EVOLUTION_DIR / "docker-compose.yml"
EVOLUTION_IMAGE = "evoapicloud/evolution-api:latest"
EVOLUTION_URL = "http://localhost:8080"


def load_config():
    if not CONFIG_PATH.exists():
        print("❌ Configuração não encontrada.")
        print("   Rode primeiro: python3 setup/setup_environment.py")
        sys.exit(1)

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def http_get_json(url, headers=None, timeout=5):
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read()
        if not payload:
            return {}
        return json.loads(payload)


def evolution_is_healthy():
    try:
        payload = http_get_json(f"{EVOLUTION_URL}/health", timeout=3)
    except Exception:
        return False

    if isinstance(payload, dict):
        if payload.get("status") == "ok":
            return True
        if payload.get("message"):
            return True
    return False


def ensure_provider(config):
    provider = config.get("whatsapp_provider")
    if provider != "evolution":
        print("❌ Este setup so deve rodar quando o provedor WhatsApp for Evolution API.")
        print(f"   Provedor atual no config.json: {provider or 'nao definido'}")
        sys.exit(1)


def read_env_value(name):
    if not ENV_PATH.exists():
        return ""

    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{name}="):
            return line.split("=", 1)[1].strip().strip("'").strip('"')
    return ""


def ensure_evolution_files():
    EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)

    api_key = read_env_value("AUTHENTICATION_API_KEY") or secrets.token_hex(16).upper()
    jwt_secret = read_env_value("JWT_SECRET") or secrets.token_urlsafe(48)

    env_content = "\n".join(
        [
            "SERVER_NAME=evolution",
            "SERVER_TYPE=http",
            "SERVER_PORT=8080",
            f"SERVER_URL={EVOLUTION_URL}",
            "DEL_INSTANCE=false",
            "DATABASE_PROVIDER=sqlite",
            "DATABASE_CONNECTION_URI=file:/evolution/store/evolution.db",
            "DATABASE_SAVE_DATA_INSTANCE=true",
            "DATABASE_SAVE_DATA_NEW_MESSAGE=true",
            "DATABASE_SAVE_MESSAGE_UPDATE=true",
            "DATABASE_SAVE_DATA_CONTACTS=true",
            "DATABASE_SAVE_DATA_CHATS=true",
            "DATABASE_SAVE_DATA_LABELS=true",
            "DATABASE_SAVE_DATA_HISTORIC=true",
            "RABBITMQ_ENABLED=false",
            "WEBSOCKET_ENABLED=false",
            "WEBHOOK_GLOBAL_ENABLED=false",
            f"AUTHENTICATION_API_KEY={api_key}",
            "AUTHENTICATION_EXPOSE_IN_FETCH_INSTANCES=true",
            f"JWT_SECRET={jwt_secret}",
            "LANGUAGE=pt-BR",
            "",
        ]
    )
    ENV_PATH.write_text(env_content, encoding="utf-8")

    compose_content = "\n".join(
        [
            "services:",
            "  evolution-api:",
            f"    image: {EVOLUTION_IMAGE}",
            "    restart: unless-stopped",
            "    env_file:",
            "      - .env",
            "    ports:",
            "      - \"8080:8080\"",
            "    volumes:",
            "      - ./store:/evolution/store",
            "",
        ]
    )
    COMPOSE_PATH.write_text(compose_content, encoding="utf-8")

    return api_key


def run_command(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, check=False)


def install_and_start():
    print("  Baixando imagem da Evolution API...")
    pull_result = run_command(["docker", "pull", EVOLUTION_IMAGE])
    if pull_result.returncode != 0:
        print("❌ Falha ao baixar a imagem da Evolution API.")
        sys.exit(1)

    print("  Subindo container com docker compose...")
    compose_result = run_command(
        ["docker", "compose", "up", "-d"],
        cwd=str(EVOLUTION_DIR),
    )
    if compose_result.returncode != 0:
        print("❌ Falha ao iniciar a Evolution API com docker compose.")
        sys.exit(1)


def wait_until_ready(timeout_seconds=120):
    started_at = time.time()
    while time.time() - started_at < timeout_seconds:
        if evolution_is_healthy():
            return True
        time.sleep(2)
    return False


def main():
    print()
    print("Instalacao da Evolution API")
    print("=" * 50)
    print()

    config = load_config()
    ensure_provider(config)

    api_key = ensure_evolution_files()

    print("  Verificando Evolution API em http://localhost:8080/health ...")
    if evolution_is_healthy():
        print("  ✅ Evolution API ja esta rodando.")
    else:
        install_and_start()
        print("  Aguardando API ficar pronta...")
        if not wait_until_ready():
            print("❌ Timeout aguardando a Evolution API responder em /health.")
            print("   Tente verificar os logs com: docker compose logs")
            sys.exit(1)
        print("  ✅ Evolution API pronta.")

    config["whatsapp_provider"] = "evolution"
    config["evolution"] = {
        "base_url": EVOLUTION_URL,
        "api_key": api_key,
        "instance_name": "operacao-ia",
    }
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("✅ Evolution API configurada!")
    print(f"  Base URL: {EVOLUTION_URL}")
    print("  API key salva em ~/.operacao-ia/config/config.json")
    print("  Proxima etapa: python3 setup/connect_whatsapp.py")
    print()


if __name__ == "__main__":
    main()
