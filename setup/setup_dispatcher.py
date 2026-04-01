#!/usr/bin/env python3
"""
Deploya o dispatcher e seus templates para ~/.operacao-ia/scripts/.
"""

from datetime import datetime
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = Path.home() / ".operacao-ia"
SCRIPTS_DIR = BASE_DIR / "scripts"
SOURCE_DISPATCHER = REPO_DIR / "scripts" / "dispatcher.py"
SOURCE_WPP = REPO_DIR / "templates" / "whatsapp_api_template.py"
SOURCE_RATE = REPO_DIR / "templates" / "rate_limiter_template.py"
SOURCE_LOG = REPO_DIR / "templates" / "dispatch_log_template.py"


def deploy_file(source, target):
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0].startswith("#!"):
        lines.insert(1, f"# Gerado automaticamente por setup_dispatcher.py em {datetime.now().isoformat()}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    target.chmod(0o755)


def main():
    print()
    print("Configuracao do Dispatcher")
    print("=" * 50)
    print()

    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    deploy_file(SOURCE_DISPATCHER, SCRIPTS_DIR / "dispatcher.py")
    deploy_file(SOURCE_WPP, SCRIPTS_DIR / "whatsapp_api_template.py")
    deploy_file(SOURCE_RATE, SCRIPTS_DIR / "rate_limiter_template.py")
    deploy_file(SOURCE_LOG, SCRIPTS_DIR / "dispatch_log_template.py")

    enviar = SCRIPTS_DIR / "enviar.sh"
    enviar.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                f"# Gerado automaticamente por setup_dispatcher.py em {datetime.now().isoformat()}",
                "# Exemplos de uso:",
                "# Dry-run simples:",
                "#   ~/.operacao-ia/scripts/dispatcher.py --message \"Oi {nome}, passando para te avisar...\" --dry-run",
                "# Disparo real com arquivo:",
                "#   ~/.operacao-ia/scripts/dispatcher.py --file ~/.operacao-ia/data/mensagem.txt",
                "# Filtrando por tag:",
                "#   ~/.operacao-ia/scripts/dispatcher.py --message \"Oi {nome}\" --tag clientes --dry-run",
                'python3 ~/.operacao-ia/scripts/dispatcher.py "$@"',
                "",
            ]
        ),
        encoding="utf-8",
    )
    enviar.chmod(0o755)

    print("✅ Dispatcher configurado!")
    print("Exemplos:")
    print("  Dry-run: ~/.operacao-ia/scripts/enviar.sh --message \"Oi {nome}\" --dry-run")
    print("  Arquivo: ~/.operacao-ia/scripts/enviar.sh --file ~/.operacao-ia/data/mensagem.txt")
    print("  Por tag: ~/.operacao-ia/scripts/enviar.sh --message \"Oi {nome}\" --tag clientes --dry-run")
    print()


if __name__ == "__main__":
    main()
