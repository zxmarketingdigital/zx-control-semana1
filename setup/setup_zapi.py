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


def validate_credentials(instance_id, token, client_token=""):
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/status"
    headers = {"User-Agent": "ZXControl/1.0"}
    if client_token:
        headers["Client-Token"] = client_token
    request = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read()
        return response.status, json.loads(body) if body else {}


def find_existing_credentials():
    """Busca credenciais Z-API existentes em locais conhecidos."""
    env_paths = [
        Path.home() / ".operacao-ia" / "config" / ".env",
        Path.home() / ".env",
    ]
    creds = {}
    for env_path in env_paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if key == "ZAPI_INSTANCE":
                creds["instance_id"] = value
            elif key == "ZAPI_TOKEN":
                creds["token"] = value
            elif key == "ZAPI_CLIENT_TOKEN":
                creds["client_token"] = value
    # Também verifica config.json existente
    if CONFIG_PATH.exists():
        try:
            existing = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            zapi = existing.get("zapi", {})
            if zapi.get("instance_id") and not creds.get("instance_id"):
                creds["instance_id"] = zapi["instance_id"]
            if zapi.get("token") and not creds.get("token"):
                creds["token"] = zapi["token"]
            if zapi.get("client_token") and not creds.get("client_token"):
                creds["client_token"] = zapi["client_token"]
        except (json.JSONDecodeError, KeyError):
            pass
    return creds


def main():
    print()
    print("Configuracao da Z-API")
    print("=" * 50)
    print()

    config = load_config()
    if not config:
        return

    # Verifica credenciais existentes
    existing = find_existing_credentials()
    instance_id = existing.get("instance_id", "")
    token = existing.get("token", "")
    client_token = existing.get("client_token", "")

    if instance_id and token:
        masked = instance_id[:8] + "..." + instance_id[-4:]
        print(f"  Credenciais Z-API encontradas: {masked}")
        try:
            reuse = input("  Usar essas credenciais? (s/n) [s]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            reuse = "s"
        if reuse not in ("n", "nao", "no"):
            print("  Reutilizando credenciais existentes.")
        else:
            instance_id = ask("Digite o ZAPI_INSTANCE_ID")
            token = ask("Digite o ZAPI_TOKEN")
            client_token = ask("Digite o ZAPI_CLIENT_TOKEN (token de seguranca da conta)")
    else:
        instance_id = ask("Digite o ZAPI_INSTANCE_ID")
        token = ask("Digite o ZAPI_TOKEN")
        client_token = ask("Digite o ZAPI_CLIENT_TOKEN (token de seguranca da conta)")

    print("  Validando conexao com a Z-API...")
    try:
        status_code, payload = validate_credentials(instance_id, token, client_token)
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
        "client_token": client_token,
        "status_url": f"https://api.z-api.io/instances/{instance_id}/token/{token}/status",
        "validated": True,
        "status_payload": payload,
    }
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("✅ Z-API configurada com sucesso!")
    print(f"  Instancia: {instance_id[:8]}...")
    print("  Credenciais salvas em ~/.operacao-ia/config/config.json")
    print()


if __name__ == "__main__":
    main()
