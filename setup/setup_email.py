#!/usr/bin/env python3
"""
Configura o envio de email via Resend e executa um teste simples.
"""

import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
RESEND_URL = "https://api.resend.com/emails"
DEFAULT_FROM_EMAIL = "onboarding@resend.dev"


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


def ask_non_empty(prompt):
    while True:
        try:
            value = input(f"{prompt}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            print("Setup cancelado.")
            sys.exit(1)

        if value:
            return value
        print("❌ Este campo nao pode ficar em branco. Tente novamente.")


def ask_email(prompt):
    while True:
        value = ask_non_empty(prompt)
        if re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]{2,}$", value):
            return value
        print("❌ Email invalido. Exemplo: nome@dominio.com.br")


def send_test_email(api_key, recipient_email):
    payload = json.dumps(
        {
            "from": DEFAULT_FROM_EMAIL,
            "to": [recipient_email],
            "subject": "Teste ZX Control — Resend conectado",
            "html": (
                "<strong>ZX Control</strong><br>"
                "Seu email foi conectado com sucesso na Semana 1."
            ),
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        RESEND_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ZXControl/1.0",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        return response.status, json.loads(body) if body else {}


def finalize_success(config, api_key, student_email, message_id):
    config["email"] = {
        "provider": "resend",
        "api_key": api_key,
        "from_email": DEFAULT_FROM_EMAIL,
        "test_recipient": student_email,
        "last_test_id": message_id,
        "test_status": "sent",
        "last_test_error": "",
    }
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("Email configurado com sucesso!")
    print("  Provedor: resend")
    print(f"  Remetente padrao: {DEFAULT_FROM_EMAIL}")
    print(f"  Email de teste enviado para: {student_email}")
    print(f"  ID do teste: {message_id}")
    print()


def finalize_with_warning(config, api_key, student_email, warning_detail):
    config["email"] = {
        "provider": "resend",
        "api_key": api_key,
        "from_email": DEFAULT_FROM_EMAIL,
        "test_recipient": student_email,
        "last_test_id": "",
        "test_status": "pending",
        "last_test_error": warning_detail,
    }
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 2)
    save_config(config)

    print()
    print("Email configurado, mas o teste nao foi confirmado agora.")
    print("  Provedor: resend")
    print(f"  Remetente padrao: {DEFAULT_FROM_EMAIL}")
    print(f"  Email configurado para: {student_email}")
    print("  Aviso: o Resend nao confirmou o envio neste momento.")
    print(f"  Detalhe: {warning_detail}")
    print("  Voce pode seguir com o setup e testar o email novamente depois.")
    print()


def main():
    print()
    print("Configuracao de Email (Resend)")
    print("=" * 50)
    print()

    config = load_config()

    api_key = ask_non_empty("Digite sua RESEND_API_KEY")
    student_email = ask_email("Digite o email onde voce quer receber o teste")
    try:
        status_code, payload = send_test_email(api_key, student_email)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        finalize_with_warning(config, api_key, student_email, body or str(exc))
        return
    except Exception as exc:
        finalize_with_warning(config, api_key, student_email, str(exc))
        return

    message_id = payload.get("id")
    if status_code != 200 or not message_id:
        finalize_with_warning(config, api_key, student_email, "resposta sem id valido do Resend")
        return

    finalize_success(config, api_key, student_email, message_id)


if __name__ == "__main__":
    main()
