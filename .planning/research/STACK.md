# Technology Stack

**Project:** ZX Control Semana 1 — Setup Operacao IA
**Researched:** 2026-04-01

## Recommended Stack

### Core Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | 3.10+ | All automation scripts, agents, monitors | Already proven in agente-ia-vendas and Mission Control. Every ZX LAB script runs on Python. Students need ONE language, not two. Note: require 3.10+ (not 3.9) for `match/case` and `tomllib` stdlib. | HIGH |
| Claude Code CLI | latest | Student interface — runs CLAUDE.md auto-executor | The entire product concept: student types nothing, Claude reads CLAUDE.md and executes. Already validated in agente-ia-vendas. | HIGH |
| Docker + Docker Compose | 28.x / v2 | Evolution API container (WhatsApp) | Required by Evolution API. Docker Desktop includes Compose v2. Students install Docker Desktop once. | HIGH |

### WhatsApp Integration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Evolution API | v2.2.0 | WhatsApp local (primary) | Free, local, no monthly cost. Docker image `atendai/evolution-api:v2.2.0`. Needs PostgreSQL + Redis alongside, but docker-compose handles this. | HIGH |
| Z-API | cloud (current) | WhatsApp fallback (8GB RAM machines) | Paid (R$97/mo) but lighter. Cloud-hosted, no Docker needed. Fallback for students whose machines cannot run Evolution. Already battle-tested in ZX LAB production. | HIGH |

**Decision:** Evolution API as default. Z-API as fallback. The setup script detects available RAM and recommends accordingly. Threshold: 16GB+ = Evolution, <16GB = Z-API.

**Evolution API docker-compose** requires:
- `atendai/evolution-api:v2.2.0` (main API)
- `postgres:15` (session storage)
- `redis:7` (cache/queue)

Total RAM: ~1.5-2GB for the stack. On 8GB machines with other apps running, this is tight, hence Z-API fallback.

### Email

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Resend | API v2 | Transactional + batch email | Free tier: 3,000/month. Dead-simple API. Python SDK `resend` 2.26.0 is mature. No SMTP config nightmares. | HIGH |

**Why not AWS SES:** Requires AWS account verification, domain setup, sandbox escape. Too much friction for Day 1. Resend = API key + done.

**Why not SendGrid/Mailgun:** Resend has the simplest DX. One API key, one function call. Already proven in ZX LAB production.

### AI Providers (Multi-Provider)

| Technology | Package | Version | Purpose | Why | Confidence |
|------------|---------|---------|---------|-----|------------|
| OpenAI | `openai` | 2.30.0 | GPT models for sales agent | Best cost/quality ratio. gpt-5.4-mini at ~$0.0001/conv. Recommended default. | HIGH |
| Google Gemini | `google-genai` | latest (GA) | Gemini models (free tier) | Free option for students on budget. Uses new unified SDK (`google-genai`), NOT deprecated `google-generativeai`. | MEDIUM |
| Anthropic | `anthropic` | 0.87.0 | Claude models for precision | Best reasoning for complex sales. Most expensive. Optional choice for premium users. | HIGH |

**Critical: google-generativeai is DEPRECATED.** Support ended Nov 2025. Use `google-genai` (the new unified GenAI SDK). This will be a common mistake in tutorials/GPT suggestions.

### Database

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| SQLite | stdlib (3.x) | Contacts, sessions, dispatch log, config | Zero setup. Built into Python. No external process. Perfect for local-first product. Already proven pattern in Mission Control dispatch-log.py and agent sessions. | HIGH |

**Why not Supabase/Postgres:** Semana 1 is local-first. No external dependencies. No accounts to create. SQLite is the right call for Day 1. Supabase comes in Semana 2+ when students need remote data.

### HTTP Client

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `requests` | 2.32.x | All HTTP calls (APIs, webhooks) | Students' scripts are simple sequential calls. No need for async complexity. `requests` is the most well-known, most debuggable, most Stack Overflow-answered library. | HIGH |

**Why not httpx:** httpx is technically superior (async support, HTTP/2), but adds complexity. These scripts make <50 requests per run. `requests` keeps the codebase approachable for students who might eventually read the code.

### Configuration

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `python-dotenv` | 1.0.x | Load `.env` files | Simple, proven, zero learning curve. Every template already uses it. | HIGH |

**Why not pydantic-settings:** Overkill for this use case. Students never touch config directly. Claude generates the `.env` file. `python-dotenv` + `os.getenv()` is sufficient and keeps the codebase simple.

### Scheduling

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `launchctl` / LaunchAgents | macOS native | Scheduled tasks on macOS | OS-level. Survives restarts. Survives crashes. Claude generates the plist files. | HIGH |
| `cron` | Linux native | Scheduled tasks on Linux | Same benefits as launchctl. Universally available. | HIGH |
| Task Scheduler | Windows native | Scheduled tasks on WSL2 | WSL2 uses cron internally. | MEDIUM |

**Why not Python `schedule` library:** Runs inside the process. If process dies, schedule dies. LaunchAgents/cron are OS-level, persistent, and restart automatically. This is a critical reliability difference for non-technical users who will not notice a crashed Python process.

**Why not APScheduler:** Same problem -- in-process. Also adds dependency complexity. OS schedulers are the right tool.

### Rate Limiting

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Custom Python (template) | n/a | WhatsApp anti-block rate limiter | Based on production `zx_rate_limiter.py`: 30/h, 150/day, 90s between messages. SQLite-backed counters. Template it, do not use a library. | HIGH |

**Why not a library:** The rate limiter is 100 lines of Python with SQLite. It is domain-specific (WhatsApp anti-block rules). No library matches these exact constraints. Already proven in production.

### Monitoring

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Custom Python (template) | n/a | Health check (WhatsApp + Email) | Based on production `health-checker.py`. Checks Evolution/Z-API status endpoint + Resend API. Sends alert via WhatsApp if something is down. | HIGH |
| LaunchAgent/cron | native | Run health check every 5min | OS-level scheduling for reliability. | HIGH |

### Supporting Libraries

| Library | Version | Purpose | When to Use | Confidence |
|---------|---------|---------|-------------|------------|
| `python-dotenv` | 1.0.x | Environment variable loading | Every script | HIGH |
| `requests` | 2.32.x | HTTP client | API calls | HIGH |
| `resend` | 2.26.0 | Email sending | Email dispatch scripts | HIGH |
| `openai` | 2.30.0 | OpenAI API | AI agent (when OpenAI selected) | HIGH |
| `google-genai` | latest | Google Gemini API | AI agent (when Gemini selected) | MEDIUM |
| `anthropic` | 0.87.0 | Anthropic API | AI agent (when Anthropic selected) | HIGH |
| `qrcode` | 8.0 | QR code generation for terminal | WhatsApp connection step | HIGH |
| `Pillow` | 11.x | Image support for qrcode | Required by qrcode for PNG output | HIGH |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| WhatsApp | Evolution API | Baileys/whatsapp-web.js | Node.js dependency, no REST API, harder to template |
| WhatsApp | Evolution API | Twilio/MessageBird | Paid per message, expensive, requires business verification |
| Email | Resend | AWS SES | Complex setup (domain verification, sandbox escape) |
| Email | Resend | SendGrid | More complex API, heavier SDK, free tier limited |
| Database | SQLite | PostgreSQL | External process, requires install, overkill for local data |
| Database | SQLite | TinyDB/JSON files | No SQL queries, no deduplication primitives, scales poorly |
| AI SDK | Direct SDKs | LangChain | Massive dependency, abstraction students cannot debug, version churn |
| AI SDK | Direct SDKs | LiteLLM | Extra dependency for a 3-provider switch statement. Not worth it. |
| Config | python-dotenv | pydantic-settings | Overkill. Students never edit config manually. |
| Scheduling | OS native | APScheduler | In-process, dies with process, not suitable for non-technical users |
| HTTP | requests | httpx | Async not needed, adds complexity, less community knowledge |

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| `google-generativeai` | DEPRECATED since Nov 2025. Use `google-genai` instead. |
| LangChain | Massive dependency tree, version incompatibilities, abstraction too thick for debugging |
| Node.js for scripts | Students would need TWO languages. Python-only is the right call. |
| Supabase (Semana 1) | External dependency. Local-first for Day 1. Supabase in Semana 2+. |
| Docker Compose v1 | Deprecated. Use `docker compose` (v2, built into Docker Desktop). |
| `pip install` globally | Use `pip install --user` or venv. But for simplicity, the setup script creates a venv. |
| Webhooks for monitoring | Requires external endpoint. Health check script polls locally instead. |

## Installation

```bash
# Create virtual environment
python3 -m venv ~/.operacao-ia/venv
source ~/.operacao-ia/venv/bin/activate

# Core (always installed)
pip install python-dotenv requests resend qrcode Pillow

# AI provider (one of these, based on student choice)
pip install openai          # Option A: OpenAI (recommended)
pip install google-genai    # Option B: Google Gemini (free tier)
pip install anthropic       # Option C: Anthropic Claude
```

## Project Structure (Student Machine)

```
~/.operacao-ia/
  venv/                    # Python virtual environment
  config/
    .env                   # All API keys and settings
    negocio.json           # Student's business data (product, checkout, etc.)
  scripts/
    bom_dia.py             # Daily good morning WhatsApp
    disparo_whatsapp.py    # Scheduled WhatsApp dispatches
    disparo_email.py       # Scheduled email dispatches
    agente_ia.py           # AI sales agent
    watcher.py             # Agent watcher (keeps agent alive)
    monitor.py             # Health check (WhatsApp + Email)
    status_matinal.py      # Daily status report
  data/
    contatos.db            # SQLite: contacts
    sessions.db            # SQLite: AI agent conversations
    dispatch.db            # SQLite: dispatch log + deduplication
  logs/
    *.log                  # Script execution logs
```

## Sources

- [Evolution API Docker docs](https://doc.evolution-api.com/v2/en/install/docker) - Installation guide, v2.2.0
- [Evolution API GitHub releases](https://github.com/EvolutionAPI/evolution-api/releases) - Version history
- [Resend Python SDK on PyPI](https://pypi.org/project/resend/) - v2.26.0, March 2026
- [OpenAI Python SDK on PyPI](https://pypi.org/project/openai/) - v2.30.0, March 2026
- [google-genai on PyPI](https://pypi.org/project/google-genai/) - New unified SDK (replaces deprecated google-generativeai)
- [Anthropic Python SDK on PyPI](https://pypi.org/project/anthropic/) - v0.87.0, March 2026
- [google-generativeai deprecation](https://github.com/google-gemini/deprecated-generative-ai-python) - Confirmed deprecated
- [Pydantic Settings docs](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) - Considered but rejected for simplicity
- Existing ZX LAB production code: `~/.zxlab-mission-control/dispatch-log.py`, `~/agente-ia-vendas/` (agente-ia-vendas repo)
