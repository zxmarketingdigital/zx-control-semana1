# Architecture Patterns

**Domain:** Guided CLI automation setup (Claude Code auto-executor)
**Researched:** 2026-04-01
**Confidence:** HIGH (based on working production reference: agente-ia-vendas + Mission Control)

## Recommended Architecture

### Overview

The system is a **conductor-driven setup** where CLAUDE.md acts as a sequential state machine that Claude Code executes step-by-step. The repo itself is a "setup kit" -- not a running application. Its output is a fully configured `~/.operacao-ia/` directory on the student's machine with running scripts, scheduled tasks, and a personalized CLAUDE.md for ongoing operation.

```
Repository (zx-control-semana1/)
  |
  |-- CLAUDE.md              <- Conductor (sequential state machine)
  |-- setup/                 <- Step scripts (executed by Claude)
  |-- templates/             <- Python templates with {{PLACEHOLDERS}}
  |-- docs/                  <- Prerequisite guides, troubleshooting
  |
  v
Student Machine Output (~/.operacao-ia/)
  |
  |-- config/                <- .env, settings.json, contacts.db
  |-- scripts/               <- Generated Python scripts (from templates)
  |-- logs/                  <- Runtime logs
  |-- data/                  <- SQLite DBs (dispatch-log, sessions, contacts)
  |-- CLAUDE.md              <- Personalized operation guide
  |-- LaunchAgents/          <- plist templates (copied to ~/Library/LaunchAgents/)
```

### Component Boundaries

There are **two distinct phases** with separate component sets:

#### Phase A: Setup-Time Components (in the repo)

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **CLAUDE.md (Conductor)** | Defines step sequence, behavior rules, error handling | Claude Code runtime (reads instructions) |
| **setup/check_prerequisites.py** | Validates Python, Node, Git, Docker are installed | OS shell (subprocess checks) |
| **setup/check_ram.py** | Determines Evolution vs Z-API path based on available RAM | OS (reads system memory) |
| **setup/install_evolution.py** | Docker pull + docker-compose up for Evolution API | Docker daemon |
| **setup/configure_zapi.py** | Z-API fallback: validates instance ID + token | Z-API REST API |
| **setup/connect_whatsapp.py** | QR code generation, connection state polling | Evolution API or Z-API |
| **setup/configure_email.py** | Validates Resend API key, sends test email | Resend API |
| **setup/test_api.py** | Validates AI provider API key (OpenAI/Gemini/Anthropic) | Provider API |
| **setup/import_contacts.py** | Parses user-provided contacts (CSV, text, manual) into SQLite | Local filesystem, SQLite |
| **setup/generate_scripts.py** | Reads templates, fills {{PLACEHOLDERS}}, writes to ~/.operacao-ia/ | Templates dir, output dir |
| **setup/configure_scheduler.py** | Creates cron entries or LaunchAgent plists for all scheduled tasks | OS scheduler (crontab or launchctl) |
| **setup/test_end_to_end.py** | Validates all integrations work, sends status via WhatsApp | All generated scripts |
| **templates/** | Python file templates with {{PLACEHOLDERS}} | Read by generate_scripts.py |

#### Phase B: Runtime Components (generated at ~/.operacao-ia/)

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **whatsapp_api.py** | Abstraction layer for WhatsApp sending (Evolution or Z-API) | Evolution API (localhost:8080) or Z-API (cloud) |
| **email_api.py** | Abstraction layer for email sending | Resend API |
| **rate_limiter.py** | Global WhatsApp rate limiting (30/h, 150/dia, 90s gap) | SQLite (rate_limiter.db), imported by all WPP senders |
| **dispatch_log.py** | Deduplication engine for all dispatches | SQLite (dispatch_log.db), imported by all senders |
| **agent.py** | AI agent core: BANT logic, multi-provider, session management | AI provider API, sessions.db |
| **watcher.py** | Polls for new WhatsApp messages, routes to agent.py | Evolution/Z-API webhook or polling, agent.py |
| **bom_dia.py** | Daily greeting dispatch | whatsapp_api.py, dispatch_log.py, rate_limiter.py |
| **disparo_whatsapp.py** | Scheduled WhatsApp dispatches to contact list | whatsapp_api.py, dispatch_log.py, rate_limiter.py, contacts.db |
| **disparo_email.py** | Scheduled email dispatches to contact list | email_api.py, dispatch_log.py, contacts.db |
| **monitor.py** | Health check every 5min: WPP connection + Email API + Agent process | whatsapp_api.py, email_api.py, OS (pgrep) |
| **status_matinal.py** | Daily morning report: everything running? | monitor.py results, whatsapp_api.py |
| **CLAUDE.md** | Personalized operation guide for ongoing use | Claude Code (future sessions) |

### Data Flow

#### Setup-Time Flow

```
Student runs: git clone && cd && claude
                    |
                    v
        Claude reads CLAUDE.md
                    |
                    v
   [Etapa 1] check_prerequisites.py
                    |
                    v
   [Etapa 2] check_ram.py --> Evolution path (16GB+) OR Z-API path (8GB)
                    |
                    v
   [Etapa 3] install_evolution.py OR configure_zapi.py
                    |
                    v
   [Etapa 4] connect_whatsapp.py --> QR Code --> Student scans
                    |
                    v
   [Etapa 5] configure_email.py --> Resend API key --> test email
                    |
                    v
   [Etapa 6] test_api.py --> AI provider key --> validate
                    |
                    v
   [Etapa 7] Claude collects business info (conversational, no script)
                    |
                    v
   [Etapa 8] import_contacts.py --> student provides contacts
                    |
                    v
   [Etapa 9] generate_scripts.py --> fills templates --> writes ~/.operacao-ia/
                    |
                    v
   [Etapa 10] configure_scheduler.py --> creates cron/LaunchAgents
                    |
                    v
   [Etapa 11] test_end_to_end.py --> validates all, sends WhatsApp status
```

#### Runtime Data Flow

```
                     INCOMING MESSAGES
                           |
              Evolution API / Z-API webhook
                           |
                           v
                      watcher.py
                      (poll loop 3s)
                           |
                           v
                       agent.py
                    (BANT + AI call)
                           |
              +------------+-------------+
              |                          |
              v                          v
         sessions.db              whatsapp_api.py
         (SQLite)                       |
                                        v
                                  rate_limiter.py
                                        |
                                        v
                                  dispatch_log.py
                                        |
                                        v
                               Evolution / Z-API
                               (send response)


                     SCHEDULED DISPATCHES
                           |
              cron / LaunchAgent (timed)
                           |
              +------------+-------------+
              |            |             |
              v            v             v
        bom_dia.py  disparo_wpp.py  disparo_email.py
              |            |             |
              v            v             v
        contacts.db   contacts.db   contacts.db
              |            |             |
              v            v             v
       rate_limiter   rate_limiter     (n/a)
              |            |             |
              v            v             v
       dispatch_log  dispatch_log  dispatch_log
              |            |             |
              v            v             v
        whatsapp_api  whatsapp_api  email_api
              |            |             |
              v            v             v
         Evo / ZAPI   Evo / ZAPI    Resend


                      MONITORING
                           |
              cron / LaunchAgent (every 5min)
                           |
                           v
                      monitor.py
                 (check WPP + Email + Agent)
                           |
                     +-----+-----+
                     |           |
                     v           v
               status OK    status FAIL
                     |           |
                     v           v
                  (noop)   alert via WPP
                             to student


                    DAILY STATUS
                           |
              cron / LaunchAgent (morning)
                           |
                           v
                   status_matinal.py
                (aggregate all checks)
                           |
                           v
                    whatsapp_api.py
                 (send report to student)
```

## Patterns to Follow

### Pattern 1: Conductor CLAUDE.md

**What:** CLAUDE.md contains numbered steps with explicit execute commands, expected outputs, and error handling branches. It is the ONLY file Claude reads to know what to do.

**When:** Always. This is the core pattern.

**Why:** The agente-ia-vendas reference proves this works. Students do zero typing. Claude follows instructions deterministically.

**Key rules extracted from reference:**
```markdown
1. Start without waiting -- do not ask to begin
2. Execute yourself -- never ask student to paste commands
3. One step at a time -- confirm before advancing
4. Simple language -- "connect WhatsApp" not "init instance"
5. Errors are yours -- diagnose before showing to student
6. Visible progress -- show [████░░░] Step X of N
7. Never show full API keys
```

### Pattern 2: WhatsApp Abstraction Layer

**What:** A single `whatsapp_api.py` that abstracts Evolution API vs Z-API behind a unified interface: `send(phone, message)`, `check_connection()`, `get_qr_code()`.

**When:** Every script that sends WhatsApp messages imports this one module.

**Why:** The student's RAM determines which provider runs. All other scripts must be provider-agnostic. The abstraction is decided at setup time via a `WHATSAPP_PROVIDER` config value.

```python
# whatsapp_api.py (simplified)
from config import WHATSAPP_PROVIDER

def send(phone: str, message: str) -> bool:
    if WHATSAPP_PROVIDER == "evolution":
        return _send_evolution(phone, message)
    elif WHATSAPP_PROVIDER == "zapi":
        return _send_zapi(phone, message)
```

### Pattern 3: Rate Limiter as Import Guard

**What:** Every WhatsApp send goes through `rate_limiter.can_send()` before executing. The rate limiter uses SQLite to track sends: 30/hour, 150/day, 90s minimum gap.

**When:** Mandatory for every WhatsApp dispatch -- bom dia, scheduled dispatches, agent responses.

**Why:** WhatsApp blocks numbers that send too fast. This is the single biggest risk for students. The rate limiter MUST be impossible to bypass accidentally.

```python
# In every script that sends WhatsApp:
from rate_limiter import can_send, record_send
from dispatch_log import should_send, log_dispatch

if can_send() and should_send(phone, msg_type):
    whatsapp_api.send(phone, message)
    record_send()
    log_dispatch(phone, msg_type, 'whatsapp', success=True)
```

### Pattern 4: Template-Based Code Generation

**What:** Python files in `templates/` use `{{PLACEHOLDER}}` syntax. During setup, `generate_scripts.py` reads templates, substitutes placeholders from collected data, and writes final scripts to `~/.operacao-ia/scripts/`.

**When:** Step 9 of the setup flow.

**Why:** Students never edit code. The template approach means complex Python logic is pre-written and battle-tested. Only configuration values change per student.

**Placeholders to support:**
```
{{WHATSAPP_PROVIDER}}    # "evolution" or "zapi"
{{EVOLUTION_API_KEY}}    # if evolution
{{ZAPI_INSTANCE_ID}}     # if zapi
{{ZAPI_TOKEN}}           # if zapi
{{RESEND_API_KEY}}       # email
{{AI_PROVIDER}}          # "openai" | "gemini" | "anthropic"
{{AI_MODEL}}             # gpt-5.4-mini | gemini-2.5-flash | claude-opus-4-6
{{AI_API_KEY}}           # AI provider key
{{STUDENT_PHONE}}        # student's WhatsApp number
{{PRODUCT_NAME}}         # product/service name
{{CHECKOUT_LINK}}        # purchase URL
{{TRIGGER_PHRASE}}       # phrase that activates agent
{{SYSTEM_PROMPT}}        # generated BANT prompt
{{BOM_DIA_MESSAGE}}      # daily greeting text
{{BOM_DIA_TIME}}         # HH:MM for daily greeting
{{DISPARO_WPP_TIME}}     # HH:MM for WPP dispatch
{{DISPARO_EMAIL_TIME}}   # HH:MM for email dispatch
{{STATUS_TIME}}          # HH:MM for morning status
```

### Pattern 5: SQLite for Everything Local

**What:** All persistent data uses SQLite databases in `~/.operacao-ia/data/`. No external database dependencies.

**When:** Contacts, dispatch log, sessions, rate limiter state.

**DBs:**
- `contacts.db` -- imported contact list (name, phone, email, tags)
- `dispatch_log.db` -- all sent messages with dedup (same schema as Mission Control)
- `sessions.db` -- AI agent conversation sessions (phone, messages JSON, last_active)
- `rate_limiter.db` -- WhatsApp send timestamps for rate limiting

**Why:** Zero infrastructure beyond what runs on the student's machine. SQLite is built into Python. No Postgres, no Supabase, no cloud DB.

### Pattern 6: Config File Over Environment Variables

**What:** A single `~/.operacao-ia/config/settings.json` holds all configuration. A `.env` file exists as backup but `settings.json` is primary.

**When:** Every script loads config from this file at startup.

**Why:** Students will never run `export VAR=value`. JSON is readable, editable by Claude in future sessions, and parseable by Python's stdlib. The personalized CLAUDE.md references this file for Claude to understand the student's setup.

```json
{
  "whatsapp_provider": "evolution",
  "evolution_api_url": "http://localhost:8080",
  "evolution_api_key": "...",
  "resend_api_key": "...",
  "ai_provider": "openai",
  "ai_model": "gpt-5.4-mini",
  "ai_api_key": "...",
  "student_phone": "5511999999999",
  "product_name": "Curso X",
  "checkout_link": "https://...",
  "trigger_phrase": "Quero saber mais",
  "schedules": {
    "bom_dia": "09:00",
    "disparo_whatsapp": "10:00",
    "disparo_email": "14:00",
    "status_matinal": "08:00",
    "monitor_interval_min": 5
  }
}
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Multiple Config Sources

**What:** Splitting config across .env, JSON, Python constants, and command-line args.

**Why bad:** Students can't find where to change things. Claude can't reliably update config in future sessions.

**Instead:** Single `settings.json` as source of truth. `.env` file generated from it only for scripts that need env vars. One function: `load_config()`.

### Anti-Pattern 2: Hardcoded Paths to Repo

**What:** Generated scripts referencing `~/projetos/zx-control-semana1/` (the setup repo).

**Why bad:** The repo is a setup tool, not a runtime dependency. Once setup is done, `~/.operacao-ia/` must be self-contained.

**Instead:** All generated scripts use `~/.operacao-ia/` paths. The repo can be deleted after setup without breaking anything.

### Anti-Pattern 3: Agent Coupled to Dispatches

**What:** Running the AI agent inside the same process as scheduled dispatches.

**Why bad:** Agent crash kills dispatches. Dispatch queue floods block agent responses. Different failure modes.

**Instead:** Agent (watcher.py) runs as its own process/LaunchAgent. Dispatches run on separate schedules. They share only `whatsapp_api.py` and `rate_limiter.py` as imported modules.

### Anti-Pattern 4: Direct API Calls Without Abstraction

**What:** Every script directly calling Evolution API or Z-API endpoints.

**Why bad:** Changing provider means editing 10+ files. Different students use different providers.

**Instead:** `whatsapp_api.py` and `email_api.py` are the only files that know about provider specifics.

### Anti-Pattern 5: Relying on Claude Code Session for Scheduling

**What:** Using Claude Code's session to keep scripts running (e.g., background `&` processes).

**Why bad:** Claude Code sessions end. Student closes terminal, everything dies. Session-scoped processes expire in ~3 days.

**Instead:** LaunchAgents (macOS) or cron (Linux) for all scheduled tasks. They survive reboots and terminal closes.

## Suggested Build Order (Dependencies)

The components have clear dependency chains that dictate build order:

### Layer 0: Foundation (no dependencies)

1. **CLAUDE.md conductor** -- the step sequence and behavior rules
2. **setup/check_prerequisites.py** -- standalone system check
3. **setup/check_ram.py** -- determines Evolution vs Z-API path
4. **docs/** -- prerequisite installation guides

### Layer 1: Connectivity (depends on Layer 0)

4. **setup/install_evolution.py** -- Docker-based Evolution install
5. **setup/configure_zapi.py** -- Z-API fallback path
6. **setup/connect_whatsapp.py** -- QR code + connection validation
7. **setup/configure_email.py** -- Resend validation + test
8. **setup/test_api.py** -- AI provider key validation

### Layer 2: Core Runtime Templates (no inter-dependency)

9. **templates/config/settings_template.json** -- config structure
10. **templates/core/whatsapp_api_template.py** -- WPP abstraction
11. **templates/core/email_api_template.py** -- email abstraction
12. **templates/core/rate_limiter_template.py** -- rate limit engine
13. **templates/core/dispatch_log_template.py** -- dedup engine
14. **templates/core/config_loader_template.py** -- settings.json reader

### Layer 3: Feature Templates (depends on Layer 2)

15. **templates/agent/agent_core_template.py** -- AI logic, multi-provider
16. **templates/agent/sessions_template.py** -- SQLite session manager
17. **templates/agent/watcher_template.py** -- message polling + routing
18. **templates/dispatch/bom_dia_template.py** -- daily greeting
19. **templates/dispatch/disparo_whatsapp_template.py** -- WPP dispatch
20. **templates/dispatch/disparo_email_template.py** -- email dispatch
21. **templates/contacts/import_contacts_template.py** -- contact parser

### Layer 4: Monitoring Templates (depends on Layer 2 + Layer 3)

22. **templates/monitor/monitor_template.py** -- health check engine
23. **templates/monitor/status_matinal_template.py** -- daily report

### Layer 5: Generators and Schedulers (depends on all templates)

24. **setup/generate_scripts.py** -- template filler + file writer
25. **setup/configure_scheduler.py** -- cron/LaunchAgent creator
26. **setup/generate_claude_md.py** -- personalized CLAUDE.md builder

### Layer 6: Validation

27. **setup/test_end_to_end.py** -- full integration test

### Build Order Rationale

- **Layer 0 first** because CLAUDE.md is the conductor -- everything else is meaningless without it.
- **Layer 1 before templates** because you need to know what works (Evolution vs Z-API) to design templates correctly.
- **Layer 2 (core abstractions) before Layer 3 (features)** because every feature imports from core. Getting whatsapp_api.py, rate_limiter.py, and dispatch_log.py right is the most critical design decision.
- **Layer 3 (features) can be built in parallel** -- agent, dispatches, and contacts are independent.
- **Layer 4 (monitoring) last among templates** because it checks everything else.
- **Layer 5 (generators) needs all templates finished** -- it reads and fills them.
- **Layer 6 (e2e test) is always last** -- validates the complete chain.

## Directory Structure: Repository

```
zx-control-semana1/
|-- CLAUDE.md                           # Conductor (main setup orchestrator)
|-- setup/
|   |-- check_prerequisites.py          # Python, Node, Git, Docker checks
|   |-- check_ram.py                    # RAM check -> Evolution or Z-API
|   |-- install_evolution.py            # Docker pull + compose
|   |-- configure_zapi.py              # Z-API instance validation
|   |-- connect_whatsapp.py            # QR code + connection state
|   |-- configure_email.py             # Resend API validation
|   |-- test_api.py                    # AI provider validation
|   |-- import_contacts.py             # Contact parsing (CSV, text, manual)
|   |-- generate_scripts.py            # Template filler -> ~/.operacao-ia/
|   |-- configure_scheduler.py         # cron/LaunchAgent setup
|   |-- generate_claude_md.py          # Personalized CLAUDE.md
|   |-- test_end_to_end.py             # Full integration test
|   |-- utils.py                       # Shared utilities (print_step, ask_user)
|-- templates/
|   |-- core/
|   |   |-- whatsapp_api_template.py   # WPP abstraction (Evolution + Z-API)
|   |   |-- email_api_template.py      # Resend abstraction
|   |   |-- rate_limiter_template.py   # 30/h, 150/day, 90s gap
|   |   |-- dispatch_log_template.py   # SQLite dedup
|   |   |-- config_loader_template.py  # settings.json reader
|   |-- agent/
|   |   |-- agent_core_template.py     # AI logic (OpenAI/Gemini/Anthropic)
|   |   |-- sessions_template.py       # SQLite session management
|   |   |-- watcher_template.py        # Message polling + agent routing
|   |-- dispatch/
|   |   |-- bom_dia_template.py        # Daily greeting
|   |   |-- disparo_whatsapp_template.py  # Scheduled WPP
|   |   |-- disparo_email_template.py  # Scheduled email
|   |-- contacts/
|   |   |-- import_contacts_template.py # Contact DB schema + parser
|   |-- monitor/
|   |   |-- monitor_template.py        # Health check engine
|   |   |-- status_matinal_template.py # Daily morning report
|   |-- scheduler/
|   |   |-- launchagent_watcher.plist  # macOS LaunchAgent for agent
|   |   |-- launchagent_monitor.plist  # macOS LaunchAgent for monitor
|   |   |-- launchagent_status.plist   # macOS LaunchAgent for status
|   |   |-- crontab_template.txt       # Linux cron entries
|   |-- claude_md_template.md          # Personalized CLAUDE.md template
|   |-- config/
|       |-- settings_template.json     # Config structure
|-- docs/
|   |-- prerequisites.md              # Installation guide
|   |-- troubleshooting.md            # Common errors + fixes
|   |-- whatsapp-providers.md         # Evolution vs Z-API comparison
|-- docker/
    |-- docker-compose.yml            # Evolution API compose file
    |-- .env.example                  # Docker env vars
```

## Directory Structure: Student Output

```
~/.operacao-ia/
|-- config/
|   |-- settings.json                 # All configuration (source of truth)
|   |-- .env                          # Generated from settings.json
|-- scripts/
|   |-- whatsapp_api.py               # WPP abstraction (provider-specific)
|   |-- email_api.py                  # Resend wrapper
|   |-- rate_limiter.py               # Global WPP rate limiter
|   |-- dispatch_log.py               # Dedup engine
|   |-- config_loader.py              # Settings reader
|   |-- agent.py                      # AI agent core
|   |-- sessions.py                   # Session management
|   |-- watcher.py                    # Message poller + agent router
|   |-- bom_dia.py                    # Daily greeting
|   |-- disparo_whatsapp.py           # Scheduled WPP dispatch
|   |-- disparo_email.py              # Scheduled email dispatch
|   |-- import_contacts.py            # Contact importer (reusable)
|   |-- monitor.py                    # Health checker
|   |-- status_matinal.py             # Morning report
|-- data/
|   |-- contacts.db                   # Contact list
|   |-- dispatch_log.db               # Send history + dedup
|   |-- sessions.db                   # Agent conversation sessions
|   |-- rate_limiter.db               # WPP send timestamps
|-- logs/
|   |-- agent.log                     # Agent activity
|   |-- dispatch.log                  # Dispatch activity
|   |-- monitor.log                   # Health check results
|-- CLAUDE.md                         # Personalized operation guide
```

## Scalability Considerations

| Concern | Semana 1 (this) | Semana 2+ (future) |
|---------|-----------------|-------------------|
| Contacts | SQLite, <1000 contacts | Same, sufficient up to 50K |
| Dispatches | cron/LaunchAgent, sequential | Same, add batch queuing if needed |
| Agent concurrency | Single-threaded polling | Add asyncio or threading if >10 concurrent chats |
| Monitoring | Simple health check | Add heartbeat 3-layer (watchdog->heartbeat->last-resort) |
| Config | settings.json | Could migrate to Supabase if multi-device needed |
| WhatsApp provider | Evolution or Z-API | Same, abstraction layer already supports both |

## Sources

- agente-ia-vendas reference repo (local: ~/agente-ia-vendas/) -- CLAUDE.md conductor pattern, setup scripts, templates -- **HIGH confidence**
- Mission Control (local: ~/.zxlab-mission-control/) -- dispatch-log.py, health-checker.py, rate limiter patterns -- **HIGH confidence**
- OpenClaw scripts (local: ~/.openclaw/workspace/scripts/) -- bom_dia, watcher, whatsapp_api patterns -- **HIGH confidence**
- [CLI UX Patterns 2025](https://medium.com/@kaushalsinh73/top-8-cli-ux-patterns-users-will-brag-about-4427adb548b7) -- first-run wizard as proven pattern -- **MEDIUM confidence**
- [Claude Code Starter](https://github.com/seaneoliver/claude-code-starter) -- CLAUDE.md template generation approach -- **MEDIUM confidence**
- [Command Line Interface Guidelines](https://clig.dev/) -- CLI design principles -- **HIGH confidence**
