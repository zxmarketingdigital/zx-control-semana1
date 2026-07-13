#!/usr/bin/env python3
"""
Setup da Semana 2: dashboard, webhooks, heartbeat e checkpoint/resume.
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path.home() / ".operacao-ia"
SCRIPTS_DIR = BASE_DIR / "scripts"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
SOURCE_FILES = [
    "dashboard.py",
    "heartbeat.py",
    "sales_webhooks.py",
    "week2_lib.py",
]


def load_config():
    if not CONFIG_PATH.exists():
        raise SystemExit("config.json nao encontrado. Rode a Semana 1 primeiro.")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def ask(prompt, default=""):
    label = f"{prompt} [{default}]: " if default else f"{prompt}: "
    try:
        value = input(label).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        raise SystemExit("Setup cancelado.")
    return value or default


def ask_bool(prompt, default=True):
    suffix = "s" if default else "n"
    answer = ask(f"{prompt} (s/n)", suffix).lower()
    return answer in {"s", "sim", "y", "yes"}


def deploy_file(source_name):
    source = REPO_DIR / "scripts" / source_name
    target = SCRIPTS_DIR / source_name
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines.insert(1, f"# Gerado automaticamente por setup_week2.py em {datetime.now().isoformat()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o755)


def deploy_templates():
    for name in ["whatsapp_api_template.py", "rate_limiter_template.py", "dispatch_log_template.py"]:
        source = REPO_DIR / "templates" / name
        target = SCRIPTS_DIR / name
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        target.chmod(0o755)


def write_script(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(0o755)


def main():
    print()
    print("Setup da Semana 2")
    print("=" * 50)
    print()

    config = load_config()
    checkpoint_module = REPO_DIR / "scripts" / "week2_lib.py"
    namespace = {}
    exec(checkpoint_module.read_text(encoding="utf-8"), namespace)
    ensure_week2_structure = namespace["ensure_week2_structure"]
    mark_checkpoint = namespace["mark_checkpoint"]

    ensure_week2_structure()
    mark_checkpoint("estrutura", "done", "Pastas da semana 2 criadas")

    print("Vamos ativar a camada visual e operacional da Semana 2.")
    webhook_port = int(ask("Porta do servidor de webhooks", str(config.get("week2", {}).get("webhook_port", 8782))))
    dashboard_port = int(ask("Porta do dashboard local", str(config.get("week2", {}).get("dashboard_port", 8783))))
    enable_hotmart = ask_bool("Ativar endpoint da Hotmart", True)
    enable_greenn = ask_bool("Ativar endpoint da Greenn", True)
    enable_kiwify = ask_bool("Ativar endpoint da Kiwify", True)
    auto_start = ask_bool("Gerar script para subir a stack da Semana 2", True)

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    for source_name in SOURCE_FILES:
        deploy_file(source_name)
    deploy_templates()
    mark_checkpoint("deploy", "done", "Scripts da semana 2 deployados")

    config.setdefault("week2", {})
    config["week2"].update(
        {
            "enabled": True,
            "webhook_port": webhook_port,
            "dashboard_port": dashboard_port,
            "platforms": {
                "hotmart": {"enabled": enable_hotmart},
                "greenn": {"enabled": enable_greenn},
                "kiwify": {"enabled": enable_kiwify},
            },
            "checkpoint_resume": True,
        }
    )
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 4)
    save_config(config)
    mark_checkpoint("config", "done", "Config da semana 2 salva no config.json")

    write_script(
        SCRIPTS_DIR / "start_week2_stack.sh",
        [
            "#!/usr/bin/env bash",
            f"# Gerado automaticamente por setup_week2.py em {datetime.now().isoformat()}",
            "mkdir -p ~/.operacao-ia/logs",
            "pkill -f 'python3 ~/.operacao-ia/scripts/sales_webhooks.py' >/dev/null 2>&1 || true",
            "pkill -f 'python3 ~/.operacao-ia/scripts/dashboard.py --serve' >/dev/null 2>&1 || true",
            f"nohup python3 ~/.operacao-ia/scripts/sales_webhooks.py --port {webhook_port} >> ~/.operacao-ia/logs/sales_webhooks.log 2>&1 &",
            f"nohup python3 ~/.operacao-ia/scripts/dashboard.py --serve --port {dashboard_port} >> ~/.operacao-ia/logs/dashboard.log 2>&1 &",
            "python3 ~/.operacao-ia/scripts/heartbeat.py --layer all >> ~/.operacao-ia/logs/heartbeat.log 2>&1",
            "echo \"Semana 2 iniciada.\"",
        ],
    )
    mark_checkpoint("scripts", "done", "Script start_week2_stack.sh criado")

    subprocess.run(
        ["python3", str(SCRIPTS_DIR / "dashboard.py"), "--build"],
        capture_output=True,
        text=True,
        check=False,
    )
    mark_checkpoint("dashboard", "done", "Dashboard inicial gerado")

    if auto_start:
        start_result = subprocess.run(
            [str(SCRIPTS_DIR / "start_week2_stack.sh")],
            capture_output=True,
            text=True,
            check=False,
        )
        mark_checkpoint("startup", "done", (start_result.stdout or start_result.stderr).strip() or "stack iniciada")

    print("✅ Semana 2 configurada!")
    print(f"  Webhooks: http://127.0.0.1:{webhook_port}/webhook/hotmart")
    print(f"  Dashboard: http://127.0.0.1:{dashboard_port}")
    print("  Script de start: ~/.operacao-ia/scripts/start_week2_stack.sh")
    print("  Checkpoint: ~/.operacao-ia/config/week2_checkpoint.json")
    print()


if __name__ == "__main__":
    main()
