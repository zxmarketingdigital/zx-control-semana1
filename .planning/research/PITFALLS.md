# Domain Pitfalls

**Domain:** Guided automation setup for non-technical users (WhatsApp + Email + AI agent)
**Researched:** 2026-04-01
**Overall confidence:** HIGH (based on production experience at ZX LAB + external research)

---

## Critical Pitfalls

Mistakes that cause abandonment, broken setups, or WhatsApp number bans.

### Pitfall 1: Docker Desktop Destroys 8GB Macs

**What goes wrong:** Evolution API in Docker on an 8GB RAM Mac consumes 1.5-3GB (Docker VM overhead + Node.js Evolution API + Chromium for WhatsApp Web). Docker Desktop itself reserves 2-4GB. The Mac swaps aggressively, beach-balls, and the student thinks their computer is broken. They close everything, Docker state corrupts, Evolution API loses the WhatsApp session.

**Why it happens:** Docker Desktop runs a full Linux VM on macOS. Even idle, it consumes 800MB-1.5GB. Evolution API v2 with a connected WhatsApp instance adds 200-500MB. Combined with macOS system processes and Claude Code (Node.js), 8GB is not enough.

**Consequences:** Student's Mac becomes unusable. They force-quit Docker. WhatsApp session disconnects. Re-setup is needed. Student loses confidence in the product on Day 1.

**Prevention:**
- Detect RAM at setup start: `sysctl -n hw.memsize` and convert to GB
- If RAM <= 8GB: skip Docker entirely, route to Z-API (cloud-based, zero local resources)
- If RAM = 16GB: proceed with Docker but set memory limit in Docker Desktop to 4GB max
- Never present Docker/Evolution as the "default" -- present Z-API as the easy path and Docker as the "advanced/free" path
- Include a "your Mac is too small for Docker" message that is NOT shameful -- frame Z-API as the recommended path

**Detection:** Mac slowing down during setup. `docker stats` showing >2GB. macOS memory pressure in yellow/red zone.

**Phase:** Prerequisites check (Phase 1 -- must be the FIRST thing the setup does)

---

### Pitfall 2: WhatsApp Number Gets Banned in the First Week

**What goes wrong:** Student configures dispatches, sends 100+ messages on Day 1 to contacts who never messaged them first. WhatsApp detects automation pattern (identical messages, rapid-fire, low response rate). Number gets temporarily or permanently banned.

**Why it happens:** Non-technical users do not understand WhatsApp's anti-spam heuristics. They think "I have 500 contacts, let me blast them all." The rate limiter prevents technical over-sending (30/h), but it does NOT prevent strategic over-sending (sending to cold contacts who will report spam).

**Consequences:** Student's WhatsApp number -- often their PERSONAL number -- gets banned. They cannot use WhatsApp for anything. Recovery takes 24h-30 days. They blame the product. This is the single highest-damage pitfall.

**Prevention:**
- **Warm-up protocol is MANDATORY, not optional:** First 10 days, max 20 NEW contacts/day. Only contacts who have messaged the student before should receive bulk dispatches initially.
- **Rate limiter defaults must be conservative:** 30/h and 150/day is already good, but new numbers should start at 10/h and 50/day for the first 2 weeks, then auto-escalate.
- **Educate DURING setup, not in docs:** When configuring dispatches, Claude must explain the ban risk in plain Portuguese, with a real example ("Se voce mandar 200 mensagens hoje, seu WhatsApp pode ser bloqueado por 30 dias").
- **Response-rate monitoring:** Track how many recipients reply. If reply rate drops below 30%, warn the student and suggest reducing volume.
- **Message variation:** Never send identical messages. Template must include personalization (at minimum, the contact's name). Randomize greetings/closings.
- **Require opt-in acknowledgment:** Before the first bulk dispatch, Claude asks: "Esses contatos ja conversaram com voce antes no WhatsApp?" If no, reduce limits drastically.

**Detection:** Rate limiter logs showing bursts. Low reply rates. WhatsApp showing "restricted" status.

**Phase:** Dispatch configuration (Phase 5-6). Rate limiter defaults in Phase 3 (WhatsApp setup).

---

### Pitfall 3: Partial Setup State With No Recovery Path

**What goes wrong:** Setup fails at step 6 of 10. Student runs `claude` again. The setup script does not know what was already done. It tries to re-create folders that exist, re-install Docker containers that are half-running, re-write config files that were partially filled. Result: duplicate processes, corrupted config, confusing errors.

**Why it happens:** Linear setup scripts assume they run once, start-to-finish. Real setups get interrupted by: Mac going to sleep, student closing terminal, Docker download taking too long, API key being wrong, internet dropping.

**Consequences:** Student is stuck in a broken state that neither a fresh start nor a retry can fix without manual intervention. They need to ask for help, which defeats the "autonomous setup" promise.

**Prevention:**
- **Idempotent steps:** Every setup step must check current state before acting. If `~/.operacao-ia/config.json` exists, read it and skip completed steps. If Docker container `evolution-api` is running, skip installation.
- **State file:** Write `~/.operacao-ia/.setup-state.json` after each completed step: `{"completed_steps": ["prerequisites", "docker", "whatsapp"], "current_step": "email", "timestamp": "..."}`.
- **Resume capability:** On re-entry, Claude reads `.setup-state.json` and says "Voce ja completou ate o passo X. Vamos continuar de onde parou?"
- **Rollback per step:** If a step fails, clean up that step's artifacts before marking it failed. Do not leave half-states.
- **Health check before resume:** Before resuming, verify that completed steps are still healthy (Docker running? WhatsApp still connected? Config files valid?).

**Detection:** Existence of `.setup-state.json` with `current_step` not equal to `"complete"`. Docker containers in `Exited` state. Config files with empty/placeholder values.

**Phase:** Core setup infrastructure (Phase 1 -- the setup runner itself must be built with idempotency from day one)

---

### Pitfall 4: API Keys Entered Wrong With No Validation

**What goes wrong:** Student pastes their OpenAI API key but includes a trailing space, a newline, or copies from a rich-text email that includes invisible Unicode characters. Or they paste their Resend API key into the OpenAI field. The key gets saved. Everything "works" during setup. Then 3 hours later, the AI agent fails silently, or emails never send.

**Why it happens:** Non-technical users copy-paste from web dashboards, emails, or screenshots. They do not understand what an API key looks like. They cannot distinguish `sk-proj-abc123` from `re_abc123` from `key-abc123`.

**Consequences:** Silent failures. Student thinks the system is broken. They do not know what an API key is, let alone how to debug one. Support burden increases.

**Prevention:**
- **Format validation:** OpenAI keys start with `sk-`. Resend keys start with `re_`. Anthropic keys start with `sk-ant-`. Google keys are 39-char alphanumeric. Validate format BEFORE saving.
- **Strip whitespace and invisible characters:** `key.strip()` is not enough. Strip `\u200b` (zero-width space), `\u00a0` (non-breaking space), `\r`, `\n`, and any non-ASCII whitespace.
- **Live validation:** After receiving each key, make a lightweight API call to verify it works. OpenAI: `GET /v1/models` with the key. Resend: `GET /api/domains`. If it fails, tell the student immediately and ask them to re-enter.
- **Visual confirmation:** After validation, show the student what was saved: "Sua chave OpenAI: sk-proj-...abc1 (verificada e funcionando)."
- **Label each prompt clearly:** "Cole aqui sua chave da OpenAI (comeca com sk-)" not just "API key."

**Detection:** API calls returning 401/403. Key format not matching expected prefix. Key length outside expected range.

**Phase:** API configuration (Phase 4). Validation functions must be built into the setup flow.

---

### Pitfall 5: macOS Permissions Block Everything Silently

**What goes wrong:** LaunchAgents are installed but never fire. Python scripts run manually but fail when triggered by launchd. Cron jobs do not execute. The student sees no errors -- things just do not happen.

**Why it happens:** macOS Sequoia (and Sonoma) enforce TCC (Transparency, Consent, and Control) aggressively. Scripts run by launchd do not inherit the user's Full Disk Access or Automation permissions. Writing to `~/Documents/` or `~/Desktop/` from a LaunchAgent fails silently. Cron is deprecated on macOS and may be removed entirely. Additionally, macOS requires explicit approval for the "controlling process" (Terminal.app, iTerm2), not just the script.

**Consequences:** Student completes setup. Everything tests fine in the terminal. Next morning, no bom-dia was sent, no status report, no health check ran. Student thinks the system is broken. It is actually a permissions issue they cannot diagnose.

**Prevention:**
- **NEVER write to TCC-protected directories:** Use `~/.operacao-ia/` for all data, logs, and scripts. Never `~/Documents/`, `~/Desktop/`, `~/Downloads/`.
- **Use LaunchAgents, not cron:** LaunchAgents are the macOS-native way. They survive sleep (coalesce missed events). Cron does not.
- **Include StandardOutPath and StandardErrorPath in every plist:** Without these, output vanishes. Point to `~/.operacao-ia/logs/`.
- **Test the LaunchAgent during setup:** After installing the plist, do `launchctl load` + force-trigger it + verify the log file was written. Do not assume it will work later.
- **Grant Full Disk Access guidance:** If any step needs broader access, show the student exactly how to grant it (System Settings > Privacy & Security > Full Disk Access > add Terminal). Use screenshot paths or step-by-step text.
- **Verify launchctl is working:** After loading, run `launchctl list | grep operacao` to confirm the agent is registered. Check exit status.
- **Fallback verification:** Schedule a test LaunchAgent that writes a timestamp to a file in 60 seconds. After 90 seconds, check if the file exists. If not, diagnose permissions.

**Detection:** LaunchAgent plist exists in `~/Library/LaunchAgents/` but `launchctl list` does not show it. Log files in `StandardOutPath` are empty or missing. Scripts work when run manually but not on schedule.

**Phase:** Scheduling setup (Phase 7). Must include a verification step, not just installation.

---

### Pitfall 6: Student Has No Mental Model -- Cannot Recover From ANY Error

**What goes wrong:** Any error message, no matter how clear to a developer, is incomprehensible to the student. "Connection refused on port 8080" means nothing. "ModuleNotFoundError: No module named 'requests'" means nothing. The student cannot Google the error, cannot interpret it, cannot fix it. They are completely stuck.

**Why it happens:** The product targets people who "nao sabem programar" (do not know how to code). They have never seen a terminal before this week. Every error is a wall.

**Consequences:** Students flood the WhatsApp group asking for help. Support burden on Rafael becomes unsustainable. Students feel the product is "too technical" despite the guided setup. Refund requests.

**Prevention:**
- **Error interception layer:** Wrap every operation in try/catch that translates errors to Portuguese plain language. "Connection refused" becomes "O Docker nao esta rodando. Abra o Docker Desktop e espere 30 segundos, depois tente de novo."
- **Self-healing where possible:** If a Python module is missing, install it automatically. If Docker is not running, start it. If a port is in use, find an alternative.
- **Known-error database:** Map the 20 most common errors to plain-language explanations and automated fixes. Store in a JSON the setup can reference.
- **"Pedir ajuda" escape hatch:** If Claude cannot resolve an error after 2 attempts, generate a diagnostic dump (system info, error log, setup state) and tell the student: "Mande isso no grupo do ZX Control e o Rafael vai resolver." Make it one-click (copy to clipboard).
- **Never show raw stack traces:** Catch them, log them to `~/.operacao-ia/logs/errors.log`, show only the human message.
- **Proactive health checks:** After each setup step, verify it worked before moving on. Do not proceed and fail 3 steps later with an unrelated-looking error.

**Detection:** Student messages in WhatsApp group with screenshots of terminal errors. Setup state stuck on the same step after multiple retries.

**Phase:** Every phase. Error handling is not a phase -- it is a cross-cutting concern that must be designed into the setup runner from Phase 1.

---

## Moderate Pitfalls

### Pitfall 7: Docker Desktop Not Installed or Wrong Version

**What goes wrong:** Student does not have Docker Desktop installed. Or they have an old version that does not support Apple Silicon properly. Or they installed Docker via Homebrew (docker CLI only) without Docker Desktop (no VM).

**Prevention:**
- Check for Docker Desktop specifically, not just `docker` CLI
- Verify `docker info` succeeds (proves the daemon is running, not just CLI installed)
- If missing, provide exact download link and step-by-step: "Baixe em docker.com/products/docker-desktop, instale, abra o app, espere o icone ficar verde"
- Detect architecture: `uname -m` -- if `arm64`, verify Docker Desktop version >= 4.x for proper Apple Silicon support

**Phase:** Prerequisites (Phase 1)

---

### Pitfall 8: WhatsApp QR Code Expires Before Student Scans

**What goes wrong:** Evolution API generates a QR code. Student does not know where to find the QR scanner in WhatsApp. They open Settings instead of Linked Devices. By the time they find it (60-90 seconds), the QR has expired. Now the terminal shows an error and they do not know how to get a new one.

**Prevention:**
- Before showing the QR, give step-by-step instructions for scanning: "Abra WhatsApp no celular > Configuracoes > Aparelhos conectados > Conectar aparelho"
- Auto-refresh the QR if it expires, with a message "O QR expirou, gerando um novo..."
- Give them 3 minutes, not the default 60 seconds
- Use a URL-based QR display (open in browser) rather than terminal ASCII art -- easier to scan

**Phase:** WhatsApp connection (Phase 3)

---

### Pitfall 9: Evolution API WhatsApp Session Disconnects Silently

**What goes wrong:** WhatsApp Web sessions disconnect after ~14 days, or when the phone's internet drops, or when WhatsApp updates. The student does not notice. Dispatches fail silently. The AI agent stops responding.

**Prevention:**
- Health monitor must check WhatsApp connection status every 5 minutes
- If disconnected, send alert via email (since WhatsApp is down) AND write to a local file the student can see
- Include re-connection instructions in the alert
- Status matinal must explicitly say "WhatsApp: CONECTADO" or "WhatsApp: DESCONECTADO -- reconecte escaneando o QR"
- The monitor script should attempt auto-reconnect before alerting

**Phase:** Health monitor (Phase 7). Connection verification in Phase 3.

---

### Pitfall 10: SQLite Database Locks Under Concurrent Access

**What goes wrong:** Rate limiter, dispatch log, AI agent sessions, and contact import all use the same SQLite database. If two processes write simultaneously, one gets "database is locked" and the operation fails.

**Prevention:**
- Use WAL (Write-Ahead Logging) mode: `PRAGMA journal_mode=WAL;` -- allows concurrent reads with one writer
- Set busy_timeout to 5000ms: `PRAGMA busy_timeout=5000;` -- retries instead of failing immediately
- Consider separate SQLite files per concern: `contacts.db`, `sessions.db`, `dispatch.db` -- eliminates cross-concern locking
- Never hold a transaction open while doing network I/O (e.g., sending a message then updating dispatch log in the same transaction)

**Phase:** Database setup (Phase 2). Must be configured correctly from the start.

---

### Pitfall 11: Student's Contact List is a Mess

**What goes wrong:** Student provides contacts in wildly inconsistent formats. Phone numbers with spaces, dashes, parentheses, country codes, without country codes. Names with emojis, special characters. CSV with wrong delimiters. Text file with no structure at all.

**Prevention:**
- Accept ANY format: CSV, TSV, plain text (one per line), pasted text
- Phone number normalization: strip all non-digits, detect country code (default +55 for Brazil), validate length (10-11 digits for BR after country code)
- Fuzzy parsing: if a line has a number and text, assume number=phone and text=name
- Show parsed results BEFORE importing: "Encontrei 47 contatos. Aqui estao os 5 primeiros: [list]. Esta correto?"
- Reject obviously wrong numbers (too short, too long) with explanation

**Phase:** Contact import (Phase 5)

---

### Pitfall 12: Z-API Monthly Cost Surprise

**What goes wrong:** Student chooses Z-API (or is routed to it due to 8GB RAM). They do not realize it costs R$97/month. After the free trial ends, their automations stop working. They blame the product.

**Prevention:**
- State the cost CLEARLY and UPFRONT during the choice: "Z-API custa R$97/mes. A Evolution API e gratuita mas precisa de 16GB de RAM."
- If the student has 16GB, strongly recommend Evolution API to avoid ongoing cost
- If they choose Z-API, remind them of the billing cycle and what happens when it expires
- Include a check in the health monitor for Z-API subscription status (API returns error when expired)

**Phase:** WhatsApp provider selection (Phase 3)

---

## Minor Pitfalls

### Pitfall 13: Python Version Conflicts

**What goes wrong:** Student has Python 3.8 (macOS default on older systems) or multiple Python installations (Homebrew, pyenv, system). `python3` points to wrong version. `pip install` goes to wrong environment.

**Prevention:**
- Check `python3 --version` explicitly. Require >= 3.10.
- Use `python3 -m pip install` instead of bare `pip install`
- Create a venv at `~/.operacao-ia/venv/` and use it for all script execution
- Shebang lines in scripts: `#!/usr/bin/env python3` (not hardcoded paths)

**Phase:** Prerequisites (Phase 1)

---

### Pitfall 14: Git Not Configured (First-Time User)

**What goes wrong:** Student does `git clone` successfully but later operations fail because `git config user.name` and `user.email` are not set. Or they do not have SSH keys and the private repo URL requires authentication.

**Prevention:**
- Use HTTPS clone URL with token, not SSH (simpler for non-technical users)
- The repo README should have the exact clone command with token embedded (or use GitHub's "Code" button HTTPS URL)
- Setup should not require any git operations beyond the initial clone

**Phase:** Pre-setup documentation (Phase 0 -- README)

---

### Pitfall 15: Claude Code CLI Not Installed or Wrong Version

**What goes wrong:** Student does not have Claude Code CLI installed. Or they have an old version that does not support the CLAUDE.md auto-execution pattern.

**Prevention:**
- README must include exact installation command: `npm install -g @anthropic-ai/claude-code`
- First line of CLAUDE.md should verify Claude Code version and warn if outdated
- Provide fallback: "Se voce nao tem o Claude Code, siga este guia manual de 5 passos"

**Phase:** Prerequisites (Phase 0 -- README)

---

### Pitfall 16: Resend Free Tier Limits Hit Unexpectedly

**What goes wrong:** Resend free tier allows 3,000 emails/month and 100 emails/day. Student configures daily dispatches to 200 contacts. After 100, emails silently fail (or return 429). Student does not notice until contacts complain they did not receive.

**Prevention:**
- During email setup, calculate daily volume: if contacts > 100 and free tier, warn about the limit
- Rate limiter for email must respect 100/day on free tier (detect tier from API response or ask student)
- Log email send failures prominently in the status report
- Suggest upgrade to Resend paid tier if volume exceeds limits

**Phase:** Email configuration (Phase 4)

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Prerequisites check | Docker not installed, wrong Python, insufficient RAM | Automated detection with clear next-steps in Portuguese |
| Core infrastructure | Partial state on retry, no idempotency | State file + resume capability from day one |
| WhatsApp setup | QR timeout, wrong provider for hardware, session drops | RAM-based routing, QR retry loop, connection health check |
| API configuration | Invalid keys, wrong fields, invisible characters | Format validation + live API verification |
| Contact import | Messy formats, wrong phone numbers | Fuzzy parser + preview before import |
| Dispatch setup | Number banned, over-sending, no warm-up | Conservative defaults + warm-up protocol + education |
| Scheduling (LaunchAgents) | Silent failures, TCC permissions, no logs | Verification test + log paths + safe directories |
| AI agent | Wrong model config, token limits, no fallback | Multi-provider with auto-failover, budget alerts |
| Health monitor | Does not detect WhatsApp disconnect, alerts fail | Multi-channel alerts (email + local file), explicit connection status |
| Error handling (cross-cutting) | Raw errors shown, student stuck | Error interception + Portuguese messages + diagnostic dump |

---

## Sources

- [Docker Desktop memory issues on macOS](https://github.com/docker/for-mac/issues/7111) -- HIGH confidence (direct GitHub issue)
- [Docker Desktop memory leak](https://github.com/docker/for-mac/issues/6120) -- HIGH confidence
- [Evolution API problems 2025](https://wasenderapi.com/blog/evolution-api-problems-2025-issues-errors-best-alternative-wasenderapi) -- MEDIUM confidence (competitor blog, but corroborates real issues)
- [Evolution API Docker docs](https://doc.evolution-api.com/v2/en/install/docker) -- HIGH confidence (official)
- [WhatsApp anti-ban practices](https://green-api.com/en/blog/reduce-the-risk-of-WA-blocking/) -- MEDIUM confidence
- [WhatsApp ban reasons 2025](https://whautomate.com/top-reasons-why-whatsapp-accounts-get-banned-in-2025-and-how-to-avoid-them/) -- MEDIUM confidence
- [WhatsApp blast without ban](https://www.ycloud.com/blog/how-to-do-whatsapp-blast/) -- MEDIUM confidence
- [macOS TCC permissions](https://angelica.gitbook.io/hacktricks/macos-hardening/macos-security-and-privilege-escalation/macos-security-protections/macos-tcc) -- HIGH confidence
- [macOS launchd tutorial](https://www.launchd.info/) -- HIGH confidence (canonical reference)
- [Apple LaunchAgent docs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html) -- HIGH confidence (Apple official)
- [Docker Desktop memory configuration](https://oneuptime.com/blog/post/2026-02-08-how-to-configure-docker-desktop-memory-and-cpu-limits-on-macos/view) -- MEDIUM confidence
- ZX LAB production experience (rate limiter, dispatch log, WhatsApp disconnections, TCC issues) -- HIGH confidence (first-party operational data)
