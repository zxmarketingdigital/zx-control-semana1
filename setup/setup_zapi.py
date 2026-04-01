#!/usr/bin/env python3
"""
Configura a Z-API como fallback para ambientes com 8GB de RAM.
"""

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"


def load_config():
    if not CONFIG_PATH.exists():
        print("Aviso: configuracao nao encontrada.")
        print("   Rode primeiro: python3 setup/setup_environment.py")
        return None
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def ask(prompt):
    while True:
        try:
            value = input(f"{prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Setup cancelado.")
            return ""

        if value:
            return value
        print("Este campo nao pode ficar em branco. Tente novamente.")


def validate_credentials(instance_id, token):
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/status"
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read()
        return response.status, json.loads(body) if body else {}


def main():
    print()
    print("Configuracao da Z-API")
    print("=" * 50)
    print()

    config = load_config()
    if not config:
        return

    instance_id = ask("Digite o ZAPI_INSTANCE_ID")
    token = ask("Digite o ZAPI_TOKEN")
    if not instance_id or not token:
        return

    try:
        status_code, payload = validate_credentials(instance_id, token)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        print(f"Aviso: as credenciais da Z-API nao foram validadas: {body or exc}")
        return
    except Exception as exc:
        print(f"Aviso: nao foi possivel validar a Z-API agora: {exc}")
        return

    if status_code != 200:
        print(f"Aviso: a Z-API respondeu com status {status_code}.")
        return

    config["whatsapp_provider"] = "zapi"
    config["zapi"] = {
        "instance_id": instance_id,
        "token": token,
        "status_url": f"https://api.z-api.io/instances/{instance_id}/token/{token}/status",
        "validated": True,
        "status_payload": payload,
    }
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("✅ Z-API configurada com sucesso!")
    print(f"  Instancia: {instance_id}")
    print("  Credenciais salvas em ~/.operacao-ia/config/config.json")
    print()


if __name__ == "__main__":
    main()
