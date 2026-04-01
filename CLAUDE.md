<!-- GSD:project-start source:PROJECT.md -->
## Project

**ZX Control — Semana 1: Setup Operação IA**

Repositório guiado (padrão `git clone && cd && claude`) que conduz alunos do ZX Control do zero até uma operação de automação com IA funcionando — WhatsApp + Email + Agente IA + Monitor — em ~1 hora, sem precisar saber programar. O Claude lê o CLAUDE.md e executa todo o setup automaticamente, perguntando apenas dados do negócio do aluno.

**Core Value:** O aluno termina a primeira sessão com automações FUNCIONANDO no WhatsApp e Email dele — disparos programados, agente IA respondendo leads, e um monitor que avisa se algo cair. O "wow moment" é ver funcionando no mesmo dia.

### Constraints

- **RAM**: Alunos com 8GB devem usar Z-API (Evolution precisa 16GB+)
- **Zero código**: Aluno NUNCA precisa editar código — Claude faz tudo
- **1 hora**: Setup completo deve ser factível em ~1h para quem já tem pré-requisitos
- **Repo privado**: Acesso apenas para alunos matriculados (GitHub invite)
- **macOS + Linux**: Suporte completo. Windows via WSL2.
- **Anti-bloqueio**: Todo disparo WhatsApp DEVE passar pelo rate limiter (30/h, 150/dia, 90s entre msgs)
- **Independência**: Agente IA roda separado dos disparos — mesma instância Evolution, sem conflito
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
- `atendai/evolution-api:v2.2.0` (main API)
- `postgres:15` (session storage)
- `redis:7` (cache/queue)
### Email
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Resend | API v2 | Transactional + batch email | Free tier: 3,000/month. Dead-simple API. Python SDK `resend` 2.26.0 is mature. No SMTP config nightmares. | HIGH |
### AI Providers (Multi-Provider)
| Technology | Package | Version | Purpose | Why | Confidence |
|------------|---------|---------|---------|-----|------------|
| OpenAI | `openai` | 2.30.0 | GPT models for sales agent | Best cost/quality ratio. gpt-5.4-mini at ~$0.0001/conv. Recommended default. | HIGH |
| Google Gemini | `google-genai` | latest (GA) | Gemini models (free tier) | Free option for students on budget. Uses new unified SDK (`google-genai`), NOT deprecated `google-generativeai`. | MEDIUM |
| Anthropic | `anthropic` | 0.87.0 | Claude models for precision | Best reasoning for complex sales. Most expensive. Optional choice for premium users. | HIGH |
### Database
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| SQLite | stdlib (3.x) | Contacts, sessions, dispatch log, config | Zero setup. Built into Python. No external process. Perfect for local-first product. Already proven pattern in Mission Control dispatch-log.py and agent sessions. | HIGH |
### HTTP Client
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `requests` | 2.32.x | All HTTP calls (APIs, webhooks) | Students' scripts are simple sequential calls. No need for async complexity. `requests` is the most well-known, most debuggable, most Stack Overflow-answered library. | HIGH |
### Configuration
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `python-dotenv` | 1.0.x | Load `.env` files | Simple, proven, zero learning curve. Every template already uses it. | HIGH |
### Scheduling
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| `launchctl` / LaunchAgents | macOS native | Scheduled tasks on macOS | OS-level. Survives restarts. Survives crashes. Claude generates the plist files. | HIGH |
| `cron` | Linux native | Scheduled tasks on Linux | Same benefits as launchctl. Universally available. | HIGH |
| Task Scheduler | Windows native | Scheduled tasks on WSL2 | WSL2 uses cron internally. | MEDIUM |
### Rate Limiting
| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Custom Python (template) | n/a | WhatsApp anti-block rate limiter | Based on production `zx_rate_limiter.py`: 30/h, 150/day, 90s between messages. SQLite-backed counters. Template it, do not use a library. | HIGH |
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
# Create virtual environment
# Core (always installed)
# AI provider (one of these, based on student choice)
## Project Structure (Student Machine)
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
