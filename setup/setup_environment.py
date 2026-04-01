#!/usr/bin/env python3
"""
Configuração do ambiente — ZX Control Semana 1
Cria ~/.operacao-ia/ com estrutura de pastas e arquivo de configuração.
"""

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
SUBDIRS = ["config", "scripts", "data", "logs"]
CONFIG_PATH = BASE_DIR / "config" / "config.json"


def ensure_psutil():
    """Instala psutil se não estiver disponível."""
    try:
        import psutil  # noqa: F401
        return True
    except ImportError:
        print("  Instalando psutil para detectar RAM do sistema...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "psutil", "--quiet"],
            capture_output=True
        )
        if result.returncode == 0:
            print("  ✅ psutil instalado.")
            return True
        else:
            print("  ⚠️  Não foi possível instalar psutil. Usando valor padrão.")
            return False


def get_ram_gb():
    """Retorna RAM total em GB. Retorna 0 se não conseguir detectar."""
    try:
        import psutil
        ram_bytes = psutil.virtual_memory().total
        return round(ram_bytes / (1024 ** 3), 1)
    except Exception:
        return 0


def choose_whatsapp_provider(ram_gb):
    """
    Escolhe provedor WhatsApp baseado na RAM disponível.
    Evolution API requer 16GB+. Z-API é mais leve (cloud).
    """
    if ram_gb >= 16:
        return "evolution"
    return "zapi"


def create_directory_structure():
    """Cria ~/.operacao-ia/ e subdiretórios."""
    created = []
    for subdir in SUBDIRS:
        path = BASE_DIR / subdir
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(str(path))

    return created


def ask(prompt, default=""):
    """Prompt simples com valor padrão opcional."""
    if default:
        full_prompt = f"  {prompt} [{default}]: "
    else:
        full_prompt = f"  {prompt}: "

    try:
        value = input(full_prompt).strip()
        return value if value else default
    except (KeyboardInterrupt, EOFError):
        print()
        print("\n  Setup cancelado.")
        sys.exit(0)


def write_config(student_name, business_name, whatsapp_provider, ram_gb):
    """Escreve o arquivo config.json."""
    config = {
        "student_name": student_name,
        "business_name": business_name,
        "whatsapp_provider": whatsapp_provider,
        "ram_gb": ram_gb,
        "output_dir": str(BASE_DIR),
        "setup_date": date.today().isoformat(),
        "phase_completed": 1
    }

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def main():
    print()
    print("Configuração do Ambiente — ZX Control Semana 1")
    print("=" * 50)
    print()

    # 1. Detectar RAM
    psutil_ok = ensure_psutil()
    ram_gb = get_ram_gb() if psutil_ok else 0

    if ram_gb > 0:
        print(f"  Memória RAM detectada: {ram_gb} GB")
    else:
        print("  Não foi possível detectar RAM — usando configuração padrão.")

    provider = choose_whatsapp_provider(ram_gb)
    if provider == "evolution":
        print(f"  Provedor WhatsApp recomendado: Evolution API (local, gratuito)")
    else:
        print(f"  Provedor WhatsApp recomendado: Z-API (cloud, leve para {ram_gb}GB RAM)")

    print()

    # 2. Criar estrutura de pastas
    print(f"  Criando pasta ~/.operacao-ia/ ...")
    created = create_directory_structure()

    if created:
        for path in created:
            short = path.replace(str(Path.home()), "~")
            print(f"  ✅ {short}")
    else:
        print(f"  ✅ Pasta ~/.operacao-ia/ já existe — mantendo estrutura.")

    print()

    # 3. Coletar dados do aluno
    print("  Agora preciso de algumas informações sobre você.")
    print()

    student_name = ask("Qual é o seu nome?")
    while not student_name:
        print("  (Nome não pode ficar em branco)")
        student_name = ask("Qual é o seu nome?")

    business_name = ask("Qual é o nome do seu negócio ou projeto?")
    while not business_name:
        print("  (Nome do negócio não pode ficar em branco)")
        business_name = ask("Qual é o nome do seu negócio ou projeto?")

    print()

    # 4. Gravar configuração
    config = write_config(student_name, business_name, provider, ram_gb)

    print("=" * 50)
    print()
    print(f"  ✅ Ambiente configurado com sucesso!")
    print()
    print(f"  Aluno:          {student_name}")
    print(f"  Negócio:        {business_name}")
    print(f"  WhatsApp:       {provider}")
    print(f"  Pasta de dados: ~/.operacao-ia/")
    print(f"  Configuração:   ~/.operacao-ia/config/config.json")
    print()
    print("  Na próxima etapa você vai conectar o WhatsApp e o Email.")
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
