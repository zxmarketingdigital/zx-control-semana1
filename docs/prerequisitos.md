# Guia de Instalação de Pré-requisitos

> Antes de começar o setup do ZX Control, instale os itens abaixo de acordo com o seu sistema operacional.
> Depois de instalar tudo, volte para o terminal e execute: `python3 setup/check_prerequisites.py`

---

## macOS

Recomendamos usar o **Homebrew** para instalar tudo. Se não tiver o Homebrew:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### Python 3.11

```bash
brew install python@3.11
```

Verifique: `python3 --version` → deve mostrar `Python 3.11.x`

### Node.js 18+

```bash
brew install node
```

Verifique: `node --version` → deve mostrar `v18.x.x` ou superior

### Git

```bash
brew install git
```

Verifique: `git --version`

### Docker Desktop

```bash
brew install --cask docker
```

Após instalar, abra o **Docker Desktop** no seu Mac e aguarde o ícone na barra de menu ficar estável (pode levar 1-2 minutos na primeira vez).

Verifique: `docker --version`

---

## Ubuntu / Debian

### Atualizar lista de pacotes

```bash
sudo apt update
```

### Python 3.11

```bash
sudo apt install python3.11 python3.11-venv python3-pip
```

Verifique: `python3.11 --version`

Se precisar que `python3` aponte para 3.11:

```bash
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Node.js 18+

```bash
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs
```

Verifique: `node --version`

### Git

```bash
sudo apt install git
```

### Docker

```bash
sudo apt install docker.io docker-compose-v2
sudo usermod -aG docker $USER
```

> **Importante:** Após rodar `usermod`, **feche e reabra o terminal** para que a permissão de grupo seja aplicada.

Verifique: `docker --version` e `docker compose version`

---

## Windows (via WSL2)

O setup do ZX Control roda dentro do **WSL2** (Windows Subsystem for Linux). Siga os passos abaixo.

### Passo 1 — Instalar o WSL2

Abra o **PowerShell como Administrador** e execute:

```powershell
wsl --install
```

Reinicie o computador quando solicitado. Após reiniciar, o Ubuntu será instalado automaticamente.

### Passo 2 — Configurar o Ubuntu no WSL2

Abra o **Ubuntu** no menu Iniciar e crie seu usuário quando solicitado.

### Passo 3 — Seguir o guia Ubuntu

Dentro do terminal Ubuntu (WSL2), siga exatamente o **guia Ubuntu/Debian** acima para instalar Python, Node, Git e Docker.

### Passo 4 — Docker Desktop para Windows (recomendado)

Para uma experiência melhor com Docker no Windows, instale o Docker Desktop:

```powershell
winget install Docker.DockerDesktop
```

Nas configurações do Docker Desktop, habilite a integração com WSL2:
> Configurações → Resources → WSL Integration → ativar sua distro Ubuntu

### Verificação final no WSL2

Dentro do terminal Ubuntu:

```bash
python3 --version   # Python 3.11.x
node --version      # v18.x.x ou superior
git --version       # qualquer versão recente
docker --version    # 20.x ou superior
```

---

## Verificação final (todos os sistemas)

Dentro da pasta do projeto, execute:

```bash
python3 setup/check_prerequisites.py
```

Você deve ver todos os itens marcados com ✅. Se algum aparecer com ❌, o próprio script mostrará o comando exato para instalar.

---

## Problemas comuns

**"python3: command not found" no macOS**

```bash
brew install python@3.11
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

**"docker: command not found" após instalar Docker Desktop**

Abra o Docker Desktop, aguarde ele iniciar completamente e tente novamente.

**"permission denied" ao rodar docker no Ubuntu**

```bash
sudo usermod -aG docker $USER
# Feche e reabra o terminal
```

**Node não encontrado após instalar com brew**

```bash
brew link node
# ou
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
```
