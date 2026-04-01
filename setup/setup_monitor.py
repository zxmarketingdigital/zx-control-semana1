#!/usr/bin/env python3
"""
Deploya o monitor, instala LaunchAgent e oferece primeiro health check.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
SCRIPTS_DIR = BASE_DIR / "scripts"
SOURCE_MONITOR = REPO_DIR / "scripts" / "monitor.py"
SOURCE_WPP = REPO_DIR / "templates" / "whatsapp_api_template.py"
SOURCE_RATE = REPO_DIR / "templates" / "rate_limiter_template.py"
SOURCE_LOG = REPO_DIR / "templates" / "dispatch_log_template.py"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def deploy_file(source, target):
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines.insert(1, f"# Gerado automaticamente por setup_monitor.py em {datetime.now().isoformat()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o755)


def main():
    print()
    print("Configuracao do Monitor")
    print("=" * 50)
    print()

    config = load_config()
    if not config.get("student_phone"):
        phone = input("Digite seu numero para receber o resumo diario (com DDD): ").strip()
        digits = "".join(ch for ch in phone if ch.isdigit())
        if not digits.startswith("55"):
            digits = "55" + digits
        config["student_phone"] = digits
        save_config(config)

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    deploy_file(SOURCE_MONITOR, SCRIPTS_DIR / "monitor.py")
    deploy_file(SOURCE_WPP, SCRIPTS_DIR / "whatsapp_api_template.py")
    deploy_file(SOURCE_RATE, SCRIPTS_DIR / "rate_limiter_template.py")
    deploy_file(SOURCE_LOG, SCRIPTS_DIR / "dispatch_log_template.py")

    install = subprocess.run(
        ["python3", str(SCRIPTS_DIR / "monitor.py"), "--install-launchagent"],
        capture_output=True,
        text=True,
        check=False,
    )
    print(install.stdout.strip() or install.stderr.strip())

    answer = input("Quer rodar o primeiro health check agora? (s/n): ").strip().lower()
    if answer in {"s", "sim", "y", "yes"}:
        run = subprocess.run(
            ["python3", str(SCRIPTS_DIR / "monitor.py"), "--now"],
            capture_output=True,
            text=True,
            check=False,
        )
        print()
        print(run.stdout.strip() or run.stderr.strip())
        if run.returncode != 0:
            raise SystemExit(run.returncode)


if __name__ == "__main__":
    main()
