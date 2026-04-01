#!/usr/bin/env python3
"""
Conecta o WhatsApp na Evolution API usando QR Code.
"""

import base64
import json
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
QR_PATH = Path("/tmp/qrcode_whatsapp.png")
INSTANCE_NAME = "operacao-ia"


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


def get_evolution_config(config):
    evolution = config.get("evolution", {})
    base_url = evolution.get("base_url") or "http://localhost:8080"
    api_key = evolution.get("api_key")
    if not api_key:
        print("❌ API key da Evolution nao encontrada no config.json.")
        print("   Rode primeiro: python3 setup/install_evolution.py")
        sys.exit(1)
    return base_url.rstrip("/"), api_key


def call_api(base_url, api_key, endpoint, method="GET", data=None, timeout=15):
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key,
    }
    payload = json.dumps(data).encode("utf-8") if data is not None else None
    request = urllib.request.Request(
        f"{base_url}{endpoint}",
        data=payload,
        headers=headers,
        method=method,
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return json.loads(body) if body else {}


def fetch_instance_names(instances):
    names = []
    for item in instances if isinstance(instances, list) else []:
        instance = item.get("instance", {}) if isinstance(item, dict) else {}
        name = (
            item.get("name")
            or item.get("instanceName")
            or instance.get("instanceName")
        )
        if name:
            names.append(name)
    return names


def ensure_instance(base_url, api_key):
    try:
        response = call_api(base_url, api_key, "/instance/fetchInstances")
        instance_names = fetch_instance_names(response)
    except Exception as exc:
        print(f"❌ Nao foi possivel listar instancias: {exc}")
        sys.exit(1)

    if INSTANCE_NAME in instance_names:
        print(f"  ✅ Instancia {INSTANCE_NAME} ja existe.")
        return

    try:
        call_api(
            base_url,
            api_key,
            "/instance/create",
            method="POST",
            data={
                "instanceName": INSTANCE_NAME,
                "integration": "WHATSAPP-BAILEYS",
                "qrcode": True,
            },
        )
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        if "already" not in body.lower():
            print(f"❌ Falha ao criar instancia: {body or exc}")
            sys.exit(1)
    except Exception as exc:
        print(f"❌ Falha ao criar instancia: {exc}")
        sys.exit(1)

    print(f"  ✅ Instancia {INSTANCE_NAME} criada.")


def extract_qr_base64(payload):
    candidates = [
        payload.get("base64"),
        payload.get("qrcode"),
        payload.get("qr"),
    ]
    nested = payload.get("qrcode")
    if isinstance(nested, dict):
        candidates.extend([nested.get("base64"), nested.get("code")])

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate
    return ""


def save_qr_image(base64_data):
    raw = base64_data.split(",", 1)[-1]
    QR_PATH.write_bytes(base64.b64decode(raw))


def open_qr_image():
    system = platform.system().lower()
    if "darwin" in system:
        command = ["open", str(QR_PATH)]
    elif "linux" in system:
        command = ["xdg-open", str(QR_PATH)]
    else:
        return

    subprocess.Popen(command)


def wait_for_connection(base_url, api_key, timeout_seconds=90):
    started_at = time.time()
    while time.time() - started_at < timeout_seconds:
        try:
            response = call_api(
                base_url,
                api_key,
                f"/instance/connectionState/{INSTANCE_NAME}",
            )
        except Exception:
            time.sleep(2)
            continue

        state = response.get("state")
        if not state and isinstance(response.get("instance"), dict):
            state = response["instance"].get("state")

        if state == "open":
            return True
        time.sleep(2)
    return False


def main():
    print()
    print("Conexao do WhatsApp")
    print("=" * 50)
    print()

    config = load_config()
    base_url, api_key = get_evolution_config(config)

    ensure_instance(base_url, api_key)

    print("  Gerando QR Code...")
    try:
        qr_response = call_api(base_url, api_key, f"/instance/connect/{INSTANCE_NAME}")
    except Exception as exc:
        print(f"❌ Falha ao gerar QR Code: {exc}")
        sys.exit(1)

    qr_base64 = extract_qr_base64(qr_response)
    if not qr_base64:
        print("❌ A Evolution API nao retornou um QR Code valido.")
        sys.exit(1)

    try:
        save_qr_image(qr_base64)
        open_qr_image()
    except Exception as exc:
        print(f"❌ Falha ao salvar/abrir QR Code: {exc}")
        sys.exit(1)

    print(f"  ✅ QR salvo em {QR_PATH}")
    print("  Escaneie o QR com o WhatsApp do celular.")
    print("  Aguardando conexao...")

    if not wait_for_connection(base_url, api_key):
        print("❌ Timeout aguardando o WhatsApp conectar.")
        print("   Rode novamente se o QR expirar.")
        sys.exit(1)

    config.setdefault("evolution", {})
    config["evolution"]["instance_name"] = INSTANCE_NAME
    config["evolution"]["connection_state"] = "open"
    config["whatsapp_provider"] = "evolution"
    config["whatsapp_connected"] = True
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("✅ WhatsApp conectado com sucesso!")
    print(f"  Instancia: {INSTANCE_NAME}")
    print("  Estado: open")
    print()


if __name__ == "__main__":
    main()
