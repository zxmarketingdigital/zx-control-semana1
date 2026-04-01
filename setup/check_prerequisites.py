#!/usr/bin/env python3
"""
Verificador de pré-requisitos — ZX Control Semana 1
Verifica Python, Node.js, Git e Docker antes de iniciar o setup.
"""

import subprocess
import sys


def run_command(cmd):
    """Executa um comando e retorna (sucesso, saída)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        output = result.stdout.strip() or result.stderr.strip()
        return result.returncode == 0, output
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def check_python():
    """Verifica Python 3.10+."""
    ok, output = run_command([sys.executable, "--version"])
    if not ok:
        ok, output = run_command(["python3", "--version"])

    if ok and output:
        # Output: "Python 3.11.4"
        parts = output.split()
        if len(parts) >= 2:
            version_str = parts[1]
            try:
                major, minor, *_ = version_str.split(".")
                major, minor = int(major), int(minor)
                if major == 3 and minor >= 10:
                    return True, version_str
                else:
                    return False, f"{version_str} (precisa 3.10+)"
            except ValueError:
                pass
    return False, None


def check_node():
    """Verifica Node.js 18+."""
    ok, output = run_command(["node", "--version"])
    if ok and output:
        # Output: "v18.17.0"
        version_str = output.lstrip("v")
        try:
            major = int(version_str.split(".")[0])
            if major >= 18:
                return True, version_str
            else:
                return False, f"{version_str} (precisa 18+)"
        except ValueError:
            pass
    return False, None


def check_git():
    """Verifica Git."""
    ok, output = run_command(["git", "--version"])
    if ok and output:
        # Output: "git version 2.39.2"
        parts = output.split()
        version_str = parts[-1] if parts else output
        return True, version_str
    return False, None


def check_docker():
    """Verifica Docker."""
    ok, output = run_command(["docker", "--version"])
    if ok and output:
        # Output: "Docker version 24.0.5, build..."
        parts = output.split()
        version_str = ""
        for i, p in enumerate(parts):
            if p == "version" and i + 1 < len(parts):
                version_str = parts[i + 1].rstrip(",")
                break
        return True, version_str or output
    return False, None


def print_install_hint(name):
    """Imprime instruções de instalação por sistema operacional."""
    hints = {
        "Python": {
            "macOS":   "brew install python@3.11",
            "Ubuntu":  "sudo apt install python3.11 python3.11-venv",
            "Windows": "winget install Python.Python.3.11",
        },
        "Node.js": {
            "macOS":   "brew install node",
            "Ubuntu":  "sudo apt install nodejs npm",
            "Windows": "winget install OpenJS.NodeJS",
        },
        "Git": {
            "macOS":   "brew install git",
            "Ubuntu":  "sudo apt install git",
            "Windows": "winget install Git.Git",
        },
        "Docker": {
            "macOS":   "brew install --cask docker",
            "Ubuntu":  "sudo apt install docker.io && sudo usermod -aG docker $USER",
            "Windows": "winget install Docker.DockerDesktop",
        },
    }

    if name not in hints:
        return

    cmds = hints[name]
    print(f"   → macOS:   {cmds['macOS']}")
    print(f"   → Ubuntu:  {cmds['Ubuntu']}")
    print(f"   → Windows: {cmds['Windows']}")


def main():
    print()
    print("Verificando pré-requisitos do ZX Control...")
    print("=" * 50)

    checks = [
        ("Python 3.10+", check_python),
        ("Node.js 18+",  check_node),
        ("Git",          check_git),
        ("Docker",       check_docker),
    ]

    all_ok = True
    results = []

    for display_name, check_fn in checks:
        ok, version = check_fn()
        results.append((display_name, ok, version))
        if not ok:
            all_ok = False

    print()
    for display_name, ok, version in results:
        if ok:
            print(f"  ✅ {display_name} {version} — OK")
        else:
            base_name = display_name.split()[0]  # "Python", "Node.js", etc.
            if version:
                print(f"  ❌ {display_name} — versão desatualizada: {version}")
            else:
                print(f"  ❌ {display_name} — não encontrado")
            print_install_hint(base_name)
            print()

    print()
    print("=" * 50)

    if all_ok:
        print("  ✅ Tudo instalado! Pronto para continuar o setup.")
        print()
        sys.exit(0)
    else:
        print("  Aviso: ainda faltam itens antes de continuar.")
        print("  Instale os itens acima e execute novamente:")
        print("     python3 setup/check_prerequisites.py")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
