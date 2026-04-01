#!/usr/bin/env python3
"""
Configura e deploya o agente IA BANT em ~/.operacao-ia/scripts/.
"""

import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
SCRIPTS_DIR = BASE_DIR / "scripts"
LOGS_DIR = BASE_DIR / "logs"
SOURCE_AGENT = REPO_DIR / "scripts" / "agent_bant.py"
SOURCE_WPP = REPO_DIR / "templates" / "whatsapp_api_template.py"
SOURCE_RATE = REPO_DIR / "templates" / "rate_limiter_template.py"
SOURCE_LOG = REPO_DIR / "templates" / "dispatch_log_template.py"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def ask(prompt, allowed=None):
    value = input(f"{prompt}: ").strip()
    if not value:
        raise SystemExit("Campo obrigatorio nao informado.")
    if allowed and value not in allowed:
        raise SystemExit(f"Valor invalido. Use: {', '.join(allowed)}")
    return value


def call_openai_test(api_key):
    payload = json.dumps(
        {
            "model": "gpt-5.4-mini",
            "messages": [{"role": "user", "content": "Responda apenas: OK"}],
            "max_completion_tokens": 20,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def call_gemini_test(api_key):
    payload = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": "Responda apenas: OK"}]}],
            "generationConfig": {"maxOutputTokens": 20},
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        data=payload,
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def call_anthropic_test(api_key):
    payload = json.dumps(
        {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 20,
            "messages": [{"role": "user", "content": "Responda apenas: OK"}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return "".join(item.get("text", "") for item in data.get("content", [])).strip()


def validate_api_key(provider, api_key):
    if provider == "openai":
        return call_openai_test(api_key)
    if provider == "gemini":
        return call_gemini_test(api_key)
    if provider == "anthropic":
        return call_anthropic_test(api_key)
    raise ValueError(provider)


def deploy_file(source, target, replacements=None):
    text = source.read_text(encoding="utf-8")
    for old, new in (replacements or {}).items():
        text = text.replace(old, new)
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines.insert(1, f"# Gerado automaticamente por setup_agent.py em {datetime.now().isoformat()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o755)


def main():
    print()
    print("Configuracao do Agente IA")
    print("=" * 50)
    print()

    config = load_config()

    ai_provider = ask("Escolha o provider de IA (openai/gemini/anthropic)", {"openai", "gemini", "anthropic"})
    ai_api_key = ask("Cole sua API key")
    agent_name = ask("Nome do agente")
    agent_tone = ask("Tom do agente (vendas/suporte/geral)", {"vendas", "suporte", "geral"})

    try:
        response = validate_api_key(ai_provider, ai_api_key)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise SystemExit(f"Falha ao validar API key: {body or exc}") from exc
    except Exception as exc:
        raise SystemExit(f"Falha ao validar API key: {exc}") from exc

    if "OK" not in response.upper():
        raise SystemExit(f"Teste da IA retornou resposta inesperada: {response}")

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    deploy_file(
        SOURCE_AGENT,
        SCRIPTS_DIR / "agent_bant.py",
        replacements={
            "{{AGENT_NAME}}": agent_name,
            "{{AGENT_TONE}}": agent_tone,
        },
    )
    deploy_file(SOURCE_WPP, SCRIPTS_DIR / "whatsapp_api_template.py")
    deploy_file(SOURCE_RATE, SCRIPTS_DIR / "rate_limiter_template.py")
    deploy_file(SOURCE_LOG, SCRIPTS_DIR / "dispatch_log_template.py")

    start_script = SCRIPTS_DIR / "start_agent.sh"
    start_script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                f"# Gerado automaticamente por setup_agent.py em {datetime.now().isoformat()}",
                "mkdir -p ~/.operacao-ia/logs",
                "if pgrep -f 'python3 ~/.operacao-ia/scripts/agent_bant.py' >/dev/null; then",
                "  echo \"Agente ja esta rodando.\"",
                "  exit 0",
                "fi",
                "nohup python3 ~/.operacao-ia/scripts/agent_bant.py >> ~/.operacao-ia/logs/agent.log 2>&1 &",
                "sleep 1",
                "echo \"Agente iniciado em background.\"",
                "",
            ]
        ),
        encoding="utf-8",
    )
    start_script.chmod(0o755)

    config["ai_provider"] = ai_provider
    config["ai_api_key"] = ai_api_key
    config["agent_name"] = agent_name
    config["agent_tone"] = agent_tone
    config["agent_port"] = config.get("agent_port", 8781)
    config["phase_completed"] = max(int(config.get("phase_completed", 1)), 3)
    save_config(config)

    start_run = subprocess.run(
        [str(start_script)],
        capture_output=True,
        text=True,
        check=False,
    )

    print("✅ Agente IA configurado com sucesso!")
    print("  Script: ~/.operacao-ia/scripts/agent_bant.py")
    print("  Start:  ~/.operacao-ia/scripts/start_agent.sh")
    print(f"  Provider: {ai_provider}")
    if start_run.stdout.strip() or start_run.stderr.strip():
        print(f"  Execucao inicial: {start_run.stdout.strip() or start_run.stderr.strip()}")
    print()


if __name__ == "__main__":
    main()
