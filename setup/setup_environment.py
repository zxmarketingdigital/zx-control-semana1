#!/usr/bin/env python3
"""
Configuração do ambiente — ZX Control Semana 1
Cria ~/.operacao-ia/ com estrutura de pastas e arquivo de configuração.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date, datetime
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


def choose_whatsapp_provider():
    """
    Sempre prioriza Evolution API.
    Z-API fica disponivel apenas como fallback manual.
    """
    return "evolution"


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


class ConfigBackupError(OSError):
    """Nao foi possivel guardar copia de seguranca do config; o original NAO foi tocado."""


def backup_config_copy(path):
    """Copia (copy2) o config para <nome>.bak-<AAAAmmdd-HHMMSS>[-N], sem sobrescrever backup existente.

    Confere que o destino existe com o mesmo tamanho. Em falha, o original fica intacto
    e levanta ConfigBackupError (so entao o chamador pode recriar o config).
    """
    path = Path(path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = None
    try:
        n = 0
        while backup is None:
            candidate = path.with_name("%s.bak-%s%s" % (path.name, stamp, "-%d" % n if n else ""))
            try:
                # O_EXCL: a criação é atômica; se outro processo pegou o nome, tenta o próximo sufixo.
                fd = os.open(str(candidate), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                n += 1
                continue
            backup = candidate
            with os.fdopen(fd, "wb") as dst, open(str(path), "rb") as src:
                shutil.copyfileobj(src, dst)
            os.chmod(str(backup), 0o600)  # backup nunca herda permissao aberta do original
        if not backup.is_file() or backup.stat().st_size != path.stat().st_size:
            raise OSError("copia de seguranca incompleta")
    except OSError as e:
        try:
            if backup is not None and backup.is_file():
                backup.unlink()
        except OSError:
            pass
        msg = (f"Não consegui salvar uma cópia de segurança de {path}: {e}. "
               "Verifique a permissão da pasta e rode de novo.")
        print(f"  ❌ {msg}")
        raise ConfigBackupError(msg) from e
    return backup


def load_existing_config():
    """Lê o config.json existente (de outro setup ou de uma execução anterior).

    Ausente -> {}. Corrompido -> backup config.json.bak-<timestamp> e {} (nunca quebra).
    """
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError, RecursionError):
        pass
    try:
        backup = backup_config_copy(CONFIG_PATH)
    except ConfigBackupError:
        sys.exit(1)  # mensagem ja impressa; config original intacto
    print(f"  ⚠️  config.json inválido — backup salvo em {backup.name}")
    return {}


def parse_phase(value):
    """Interpreta phase_completed de forma tolerante: 5, 5.0, "5", "week5", "semana 5", "phase5". Invalido = 0."""
    if isinstance(value, bool):
        return 0
    try:
        number = float(value)
    except OverflowError:
        number = float("inf") if value > 0 else 0.0  # inteiro gigante: maior que qualquer fase, nunca sobrescreve
    except (TypeError, ValueError):
        achou = re.search(r"\d+(?:\.\d+)?", str(value))
        number = float(achou.group()) if achou else 0
    if number != number or number == float("-inf"):
        return 0
    return number


def write_config(student_name, business_name, whatsapp_provider, ram_gb):
    """Escreve o arquivo config.json, preservando o que já existir (outro setup) e sem regredir phase_completed."""
    config = load_existing_config()
    phase = parse_phase(config.get("phase_completed", 0))
    config.update({
        "student_name": student_name,
        "business_name": business_name,
        "whatsapp_provider": whatsapp_provider,
        "ram_gb": ram_gb,
        "output_dir": str(BASE_DIR),
        "setup_date": date.today().isoformat(),
    })
    if phase < 1:  # nunca reduz um phase_completed maior vindo de outro setup
        config["phase_completed"] = 1

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Grava em arquivo temporário no mesmo diretório e troca com os.replace: uma falha no meio
    # nunca deixa o config válido do aluno truncado. realpath mantém config.json que é symlink.
    destino = os.path.realpath(str(CONFIG_PATH))
    tmp = "%s.tmp-%d" % (destino, os.getpid())
    try:
        try:
            os.unlink(tmp)  # sobra de execucao interrompida
        except FileNotFoundError:
            pass
        with os.fdopen(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, destino)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise

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

    provider = choose_whatsapp_provider()
    print("  Provedor WhatsApp padrao: Evolution API (local, gratuito)")
    if ram_gb > 0 and ram_gb < 8:
        print("  ⚠️  Aviso: abaixo de 8GB de RAM a Evolution pode ficar instavel.")
        print("  ⚠️  Se precisar, voce pode usar Z-API depois como fallback manual.")
    elif ram_gb >= 8 and ram_gb < 16:
        print("  ⚠️  Aviso: 8GB de RAM e o minimo recomendado para a Evolution rodar bem.")
        print("  ⚠️  16GB ou mais e o ideal para maior estabilidade.")
    elif ram_gb >= 16:
        print("  ✅ Sua memoria esta em uma faixa ideal para rodar a Evolution com mais estabilidade.")
    else:
        print("  ⚠️  Nao foi possivel medir a RAM. A Evolution seguira como padrao.")

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
    print(f"  Fallback:       zapi (opcional)")
    print(f"  Pasta de dados: ~/.operacao-ia/")
    print(f"  Configuração:   ~/.operacao-ia/config/config.json")
    print()
    print("  Na próxima etapa você vai conectar o WhatsApp e o Email.")
    print()

    sys.exit(0)


if __name__ == "__main__":
    main()
