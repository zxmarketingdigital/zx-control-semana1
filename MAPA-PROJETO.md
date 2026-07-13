# Mapa do Projeto — ZX Control · Semana 1 (Setup Operação IA)

> **Como o projeto funciona por dentro.** Doc vivo: leio ao começar aqui em vez de re-explorar.
> Código muda — ponto de partida rápido. **Verificar contra o código atual antes de afirmar como fato.**
> Complementa: `CLAUDE.md` (regras/roteiro do instrutor) · `HISTORICO-SESSOES.md` (o que mudou). Seed: 2026-07-08.
>
> ⚠️ **Repo PÚBLICO** (`zxmarketingdigital/zx-control-semana1`, visibility `PUBLIC` verificado) — aluno clona com `git clone`. **Nunca commitar segredo aqui.** Tokens/API keys do aluno vivem só na máquina dele em `~/.operacao-ia/config/config.json` (fora do repo).

## Visão geral

Repositório de **setup guiado da Semana 1 do ZX Control** (mentoria de 30 dias). O aluno clona, roda `claude`, digita **`INICIAR SETUP`**, e o Claude Code conduz **10 etapas** rodando os scripts `setup/*.py` — o aluno nunca digita comando nem edita código. Ao final ele tem, na própria máquina, uma "Operação IA": WhatsApp + Email conectados, agente IA de vendas (BANT) respondendo leads, disparos programados com rate-limiter anti-bloqueio e um monitor diário.

O `CLAUDE.md` é o **roteiro do instrutor** (não regras de dev): mensagem de boas-vindas, 10 etapas com barra de progresso, textos de confirmação por etapa e regras de comportamento ("execute você mesmo", "uma etapa por vez", "nunca mostre API keys").

**Duplo propósito do repo** (verificado): além do setup, `docs/index.html` é a **área de membros v1** (SPA) publicada no Cloudflare Pages em `zx-control.zxlab.com.br`.

## Stack

- **Python 3.10+** (stdlib apenas nos scripts de setup: `urllib`, `sqlite3`, `http.server`, `subprocess`; `psutil` instalado on-the-fly para detectar RAM).
- **WhatsApp:** Evolution API local (Docker, `localhost:8080`) como **padrão**; Z-API como fallback opcional; `uaizap` também suportado no template de API (`templates/whatsapp_api_template.py`).
- **Email:** Resend (3.000 envios/mês grátis).
- **Agente IA:** multi-provider — OpenAI / Google Gemini / Anthropic (escolhido no setup).
- **Persistência:** SQLite local em `~/.operacao-ia/data/` (nada de nuvem no lado do aluno).
- **Área de membros (`docs/`):** HTML/CSS/JS estático (Inter + JetBrains Mono), auth via Edge Function Supabase, deploy Cloudflare Pages.
- **Pré-requisitos do aluno:** Python 3.10+, Node 18+, Git, Docker 20+, 8GB RAM mín. (16GB+ ideal). Ver `docs/prerequisitos.md`.

## Entrypoints — o setup do aluno (`setup/*.py`, chamados pelo CLAUDE.md)

Cada script é executado pelo Claude na etapa correspondente. Todos criam/leem `~/.operacao-ia/config/config.json`.

| Etapa | Script | O que faz |
|-------|--------|-----------|
| 1 | `check_prerequisites.py` | Verifica Python / Node / Git / Docker |
| 2 | `setup_environment.py` | Detecta RAM (psutil), pede nome + negócio, cria `~/.operacao-ia/{config,scripts,data,logs}` e grava `config.json` (`phase_completed: 1`). Provider WhatsApp **hardcoded `evolution`** (`choose_whatsapp_provider()` sempre retorna `"evolution"`) |
| 3 | `install_evolution.py` → `connect_whatsapp.py` (→ `setup_zapi.py` fallback) | Sobe Evolution local e conecta via QR Code; Z-API só se Evolution não puder |
| 4 | `setup_email.py` | Pede `RESEND_API_KEY` + email de teste, envia teste, grava `email.test_status` (`sent`/`pending`) no config |
| 6 | `setup_agent.py` | Pede provider IA + API key + nome/tom do agente, valida a key com chamada de teste, **deploya** `agent_bant.py` para `~/.operacao-ia/scripts/` e gera `start_agent.sh` |
| 7 | `import_contacts.py` | Aceita CSV ou texto colado, normaliza telefones, grava `data/contacts.db` (+ backup `contacts.csv`) |
| 8 | `setup_dispatcher.py` | Deploya `dispatcher.py` + templates (rate limiter, dispatch log, whatsapp api) e gera atalho `enviar.sh` |
| 9 | `setup_monitor.py` | Deploya `monitor.py` + instala LaunchAgent `br.zxlab.operacao-ia.monitor` (status matinal ~8h) |
| — | `setup_week2.py` | Semana 2: copia `dashboard.py`, `heartbeat.py`, `sales_webhooks.py`, `week2_lib.py` p/ `~/.operacao-ia/scripts/` + checkpoint/resume |

**Mecânica de deploy** (`setup_agent.py::deploy_file`): copia o arquivo de `scripts/` do repo → `~/.operacao-ia/scripts/`, substituindo placeholders `{{AGENT_NAME}}` / `{{AGENT_TONE}}` (`.replace`). É por isso que `scripts/*.py` são "fonte" e o que roda de verdade fica em `~/.operacao-ia/scripts/`.

## Fontes de runtime (`scripts/` → deployados em `~/.operacao-ia/scripts/`)

- `agent_bant.py` — agente IA de vendas. HTTP server (`BaseHTTPRequestHandler`, porta default **8781**), sessões em `data/sessions.db` (TTL **1800s**), lógica BANT. Importa os 3 templates. Placeholders `{{AGENT_NAME}}`/`{{AGENT_TONE}}` preenchidos no deploy.
- `dispatcher.py` — disparos WhatsApp em lote. CLI (`--message`/`--file`, `--tag`, `--dry-run`). Lê `contacts.db`, passa por rate limiter + dispatch log antes de enviar.
- `monitor.py` — health check + status matinal.
- **Semana 2:** `dashboard.py` (HTML local), `heartbeat.py` (3 camadas), `sales_webhooks.py` (Hotmart/Greenn/Kiwify), `week2_lib.py` (utilitários).
- `scripts/sync_asaas_purchases.py` — **⚠️ NÃO faz parte do fluxo do aluno.** É um one-shot **interno ZX LAB**: lê `~/.asaas-connector/events.json`, filtra pagamentos "ZX Control", faz upsert em `contacts` + insert idempotente em `purchases` no CRM Supabase. Ferramenta operacional que ficou hospedada aqui (ligada ao auth real do ZX Control — ver `reference feedback_zxcontrol_auth_real_pattern`).

## Templates (`templates/`)

- `whatsapp_api_template.py` — `send_whatsapp(phone, text, config)` abstrai **evolution** (`POST {base}/message/sendText/{instance}` com header `apikey`), **zapi** (`api.z-api.io/.../send-text`) e **uaizap** (`zxlab.uazapi.com/send/text`).
- `rate_limiter_template.py` — `ZAPIRateLimiter` em SQLite (`rate_limiter.db`): **30/h, 150/dia, 90s entre msgs**. `can_send()` / `record_send()` / contextmanager `sending()`.
- `dispatch_log_template.py` — dedup por `sha256(content)`, janela **24h**: `should_send()` / `log_dispatch()` em `dispatch_log.db`.
- `claude_md_template.md` — template de CLAUDE.md personalizado do aluno.

## Modelo de dados (SQLite em `~/.operacao-ia/data/` — na máquina do aluno)

| Arquivo | Papel |
|---------|-------|
| `config/config.json` | Config central: `student_name`, `business_name`, `whatsapp_provider`, `ram_gb`, `phase_completed`, blocos `evolution`/`zapi`/`email`/agente + API keys do aluno |
| `data/contacts.db` (+ `contacts.csv`) | Contatos importados (dispatcher lê daqui) |
| `data/sessions.db` | Sessões do agente BANT (TTL 1800s) |
| `data/rate_limiter.db` | Registro de envios p/ rate limiting |
| `data/dispatch_log.db` | Dedup de disparos (hash + timestamp + tipo) |

## Área de membros v1 (`docs/`)

- `docs/index.html` (~4.4k linhas) — SPA da área de membros v1, deploy **Cloudflare Pages → `zx-control.zxlab.com.br`**.
- `docs/_redirects` = `/* /index.html 200` (catch-all SPA).
- **Auth server-side:** chama Edge Function `check-zxcontrol-access` no Supabase `pnfvlszwlumetdjsuktj` (valida email contra `purchases`, `refunded=false AND access_blocked=false`). **Sem anon key/JWT nem senha no HTML** (verificado). Estado de login em `localStorage` (`zxcontrol_auth`, migrando do legado `zxcontrol_s1`).
- `docs/prerequisitos.md`, `docs/semana2.md`, `docs/session-handoff-2026-04-01.md` — docs de apoio.

## Integrações externas

- **Evolution API** (Docker local `:8080`) · **Z-API** (cloud, fallback) · **UAIZAP** (`zxlab.uazapi.com`).
- **Resend** (email).
- **OpenAI / Gemini / Anthropic** (agente IA).
- **Supabase** `pnfvlszwlumetdjsuktj` (só a área de membros e o script interno de sync).
- **Hotmart / Greenn / Kiwify** (webhooks, Semana 2).

## Gotchas / armadilhas conhecidas

- **`CLAUDE.md` tem bloco "Estado Atual (Sessão 2026-04-08)" DESATUALIZADO** (a verificar/limpar): fala em corrigir bugs em `area-membros.html` (2255 linhas) — **esse arquivo não existe no repo**; a área de membros real é `docs/index.html` (~4.4k linhas). Conteúdo de outra sessão que vazou para o roteiro do instrutor; pode confundir o Claude do aluno.
- **`.claude/launch.json`** serve a **raiz do repo** em `python3 -m http.server 7890` como "area-membros" — mas o `index.html` está em `docs/`, não na raiz. Config provavelmente **quebrada/obsoleta** (a verificar) — para servir a área de membros localmente, apontar `--directory docs`.
- **Provider WhatsApp é sempre `evolution`** no `setup_environment.py` (retorno hardcoded). Z-API só entra por caminho manual na Etapa 3.
- **Repo público:** skills que o aluno precisa devem ser **embutidas no repo e instaladas por cópia local**, nunca `claude skill install http…`/`git clone` de repo externo que pode dar 404 (ver `feedback_setup_skill_embutida_nao_repo_externo`). Ao mexer, `grep` por `skill install http`, `git clone`, `cargo/pip/npm install` e validar cada URL/pacote.
- **`sync_asaas_purchases.py` não é do aluno** — é interno ZX LAB; não confundir com o fluxo de setup.
- `graphify-out/` e `.wrangler/` são gitignored (não vão pro repo público).
- Todo disparo WhatsApp **tem** que passar pelo rate limiter (30/h · 150/dia · 90s) e pelo dispatch log — o agente roda em processo separado do dispatcher pra não conflitar.

## Comandos

```bash
# Aluno (fluxo real):
git clone https://github.com/zxmarketingdigital/zx-control-semana1.git
cd zx-control-semana1 && claude          # depois digitar: INICIAR SETUP

# Setup rodado etapa a etapa pelo Claude (exemplos):
python3 setup/check_prerequisites.py
python3 setup/setup_environment.py
python3 setup/setup_week2.py             # Semana 2

# Primeiro disparo (dry-run obrigatório):
~/.operacao-ia/scripts/enviar.sh --message "Oi {nome}, ..." --dry-run

# Servir área de membros localmente (docs/):
python3 -m http.server 7890 --directory docs

# Deploy área de membros (Cloudflare Pages → zx-control.zxlab.com.br): via docs/

# Verificar visibilidade (deve ser PUBLIC):
gh repo view zxmarketingdigital/zx-control-semana1 --json visibility
```

## Memórias relacionadas
- `feedback_zxcontrol_auth_real_pattern` — auth contra `purchases` + bloqueio individual (Edge Function `check-zxcontrol-access`).
- `feedback_setup_skill_embutida_nao_repo_externo` — skills embutidas, nunca repo externo.
- Regra global `~/CLAUDE.md`: "Repos de Setup de Aluno → SEMPRE Public".
