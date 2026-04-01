# Feature Landscape

**Domain:** Guided CLI automation setup for non-technical mentorship students (WhatsApp + Email + AI Agent)
**Researched:** 2026-04-01
**Overall confidence:** HIGH (based on existing reference product agente-ia-vendas + production ZX LAB systems + domain research)

---

## Table Stakes

Features users expect. Missing = student feels lost, setup fails, or they abandon before "wow moment."

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Auto-start on clone (CLAUDE.md triggers immediately) | Student does `git clone && cd && claude` and NOTHING else. Any manual step = failure for non-technical audience. Reference product already does this. | Low | CLAUDE.md first lines must force Claude to begin without waiting for user input |
| Visual progress indicator per step | Non-technical users panic without progress feedback. `[####....] Etapa 3 de 10` reduces anxiety and prevents "is it stuck?" questions. | Low | Emoji-based progress bar in terminal, not a real GUI |
| Prerequisite checker with auto-install | Student doesn't know what Python or Docker is. Script must detect missing deps and install them OR give a single copy-paste instruction. | Medium | Python, Node, Git, Docker (if Evolution). Handle brew/apt/winget. |
| WhatsApp connection via QR code with status validation | This is the "proof it works" moment. QR code scan is familiar (WhatsApp Web pattern). Must validate connection state before advancing. | Medium | Evolution API local (preferred) or Z-API cloud (fallback for 8GB RAM machines) |
| Email connection with send-test | Student must SEE an email arrive in their inbox during setup. Abstract "configured" messages don't build trust. | Low | Resend API key + domain verification. Test email to student's own address. |
| Contact import (paste text, CSV, or type manually) | Student needs contacts IN the system to see dispatches work. Without contacts = dead system on Day 1. | Medium | Parse multiple formats: raw phone numbers, CSV, comma-separated. Normalize to E.164. Store in SQLite. |
| Rate limiter on ALL WhatsApp sends | WhatsApp bans numbers that send too fast. If student gets banned on Day 1, product is dead. This is invisible but critical. | Medium | 30/hour, 150/day, 90s between messages. Must wrap ALL send functions. Non-negotiable. |
| Dispatch deduplication (SQLite log) | Sending the same message twice to the same person = amateur hour. Students will re-run setups, trigger dispatches multiple times. | Medium | SQLite dispatch_log table with contact+message+date dedup |
| End-to-end validation test | Student must see "everything works" confirmation. Not just "I configured it" but actual test messages sent and verified. | Medium | Send test WhatsApp + test email + verify agent responds + verify monitor runs |
| Error recovery without student intervention | Non-technical user sees a traceback = they close terminal. Claude must catch errors, diagnose, fix, and retry silently. | High | Try/except in all setup scripts. Claude CLAUDE.md rules: "errors are yours, fix before showing user" |
| Plain language (zero jargon) | "Conectar WhatsApp" not "iniciar instancia Evolution". "Chave da IA" not "API key do provider". Portuguese throughout. | Low | CLAUDE.md behavioral rules. All user-facing strings in PT-BR. |
| Personalized CLAUDE.md for student's business | After setup, student has a CLAUDE.md with THEIR product name, THEIR contacts, THEIR schedule. Makes it feel custom, not generic. | Medium | Template substitution with collected business data |

## Differentiators

Features that set ZX Control apart from Udemy courses, Typebot setups, and SaaS platforms. Not expected, but create "wow" moments.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| AI WhatsApp agent (BANT, multi-provider) running on Day 1 | Competitors teach chatbots over weeks. Student has a real AI sales agent responding to leads within the first session. This is THE differentiator. | High | Multi-provider (OpenAI/Gemini/Anthropic), BANT methodology, SQLite sessions, multi-turn conversations |
| Scheduled dispatches with flexible content (not just sales alerts) | Most automation products assume e-commerce. ZX Control students are consultants, agencies, coaches -- they need generic communication infra (follow-up, content, reminders), not just "sale notification." | Medium | Cron/LaunchAgent scheduling. Template-based content. Student defines what to send and when. |
| "Bom dia" automatic daily message | Small but powerful. Student's WhatsApp sends a daily greeting to their team/clients automatically. Immediate visible proof the system works EVERY DAY. | Low | Single cron job, configurable message and time, configurable recipient list |
| Health monitor with WhatsApp alerts | Student gets a WhatsApp message if anything breaks. They never need to open a terminal to know something is down. Proactive, not reactive. | Medium | 5-minute health check cycle. Checks: WhatsApp connected, email API responding, agent running, cron active. Alerts to student's WhatsApp. |
| Daily status report via WhatsApp | Every morning: "Your system: WhatsApp OK, Email OK, Agent responded to 3 leads yesterday, 12 dispatches sent." Student sees value without touching the computer. | Medium | Aggregates from SQLite logs. Scheduled morning message. Formatted for WhatsApp readability. |
| Checkpoint/resume setup (survive disconnection) | Student's internet drops, laptop closes, Claude session ends. When they come back and run `claude` again, setup resumes from where it stopped -- not from scratch. | High | State file (JSON) tracking completed steps. CLAUDE.md reads state on load and skips completed steps. |
| Automatic RAM detection for WhatsApp provider selection | Instead of asking "do you have 16GB RAM?", detect it. Auto-select Evolution (free, local) for 16GB+ or Z-API (paid, lighter) for 8GB. Removes a confusing decision from the student. | Low | `sysctl hw.memsize` on macOS, `/proc/meminfo` on Linux. Simple threshold check. |
| wa.me link generation for student's product | At the end of setup, student gets a ready-to-share WhatsApp link (`wa.me/number?text=trigger`) for their stories, ads, and posts. Bridges setup to actual business use. | Low | Already in reference product. Encode trigger message, present formatted link. |

## Anti-Features

Features to explicitly NOT build in Week 1. Each has a reason and a "what to do instead."

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Web dashboard / GUI | Students are in Claude Code terminal. Adding a web UI doubles complexity, introduces auth, hosting, CORS. Week 2 deliverable. | Daily WhatsApp status report gives same visibility without a browser |
| Integration with Hotmart/Greenn/Kiwify | Sales platform sync requires webhooks, payment status parsing, refund handling. Massive scope. Week 2. | Student imports contacts manually. Works for ALL business types, not just infoprodutores. |
| Google Sheets sync for contacts | Adds OAuth2 complexity, Google API quotas, sheet formatting assumptions. Non-technical users will mess up sheet structure. | SQLite local + paste/CSV import. Zero external dependencies. |
| CRM with contact management UI | Full CRM is a product, not a feature. Week 4 bonus territory. | SQLite tables with basic contact fields. Claude can query them via natural language. |
| Multi-number WhatsApp (multiple instances) | One number per student is already complex enough. Multi-number = multi-Evolution, port conflicts, routing logic. | Single WhatsApp number. Agent + dispatches share the same instance (no conflict if rate-limited). |
| AI-generated copy / content creation | Writing copy with AI is a different skill. Mixing it with infrastructure setup creates cognitive overload. Week 3. | Student provides their own message templates. Claude helps write them conversationally during setup, but no auto-generation system. |
| Custom domain email (student@theirdomain.com) | DNS configuration is a nightmare for non-technical users. Resend requires domain verification, SPF, DKIM records. | Use Resend with their default domain for testing. Custom domain is a Week 2+ optimization. |
| Skills system (/vendas, /status commands) | Custom slash commands require Claude Code plugin knowledge, skill files, testing. Premature for Week 1. | CLAUDE.md already lets students ask Claude anything in natural language. Skills formalize this in Week 4. |
| Windows native support (without WSL) | Python + Docker + Evolution on native Windows is a compatibility nightmare. Not worth the engineering cost for likely <10% of students. | Require WSL2 for Windows users. Provide WSL2 install guide as prerequisite step. |
| Automatic retry/reconnection for WhatsApp disconnects | WhatsApp disconnects are common (phone off, QR expires). Auto-reconnect requires persistent daemon, state management, edge cases. | Monitor DETECTS disconnect and alerts student. Student re-scans QR with Claude's help. Simple and reliable. |

## Feature Dependencies

```
Prerequisite Checker ─────────────────────────┐
                                               v
                              WhatsApp Connection (QR)
                                       │
                         ┌─────────────┼─────────────┐
                         v             v             v
                   Rate Limiter   AI Agent      Dispatches
                         │             │             │
                         v             v             v
                   Dedup Log      Sessions     Contact Import
                         │             │             │
                         └──────┬──────┘─────────────┘
                                v
                         Health Monitor
                                │
                                v
                         Daily Status Report
                                │
                                v
                    Personalized CLAUDE.md
                                │
                                v
                      End-to-End Test
```

**Key dependency chains:**

1. **Prerequisites** must pass before anything else installs
2. **WhatsApp connection** gates rate limiter, agent, and dispatches (all need a working WPP instance)
3. **Rate limiter** must exist before ANY dispatch or agent send (anti-ban protection)
4. **Contact import** must happen before dispatches can run (no contacts = nothing to send)
5. **Email connection** is independent of WhatsApp -- can run in parallel
6. **Health monitor** depends on all services being configured (monitors what exists)
7. **Daily status** depends on monitor + dispatch log (aggregates their data)
8. **Personalized CLAUDE.md** is the last step -- needs all business data collected during setup
9. **End-to-end test** is the absolute final step -- validates everything

## MVP Recommendation

**Prioritize (core "wow moment" path):**

1. Auto-start + progress indicator + prerequisite check (the first 30 seconds)
2. WhatsApp connection via QR code (the "it's real" moment)
3. Email connection with test send (second proof of life)
4. Rate limiter + dedup log (invisible protection layer)
5. Contact import (gives dispatches something to work with)
6. AI WhatsApp agent with BANT (THE differentiator, biggest wow)
7. Scheduled dispatches WhatsApp + Email (immediate daily value)
8. Bom dia automático (daily proof of life)
9. Health monitor + daily status report (ongoing confidence)
10. Personalized CLAUDE.md + end-to-end test (polish and closure)

**Defer to later in Week 1 if time-constrained:**

- Checkpoint/resume (valuable but adds state management complexity -- implement after core flow works)
- Automatic RAM detection (nice-to-have, can ask the question instead)

**Defer to Week 2+:**

- Dashboard HTML, sales platform integrations, Google Sheets, CRM, skills system (see Anti-Features)

## Competitive Landscape

| Competitor Type | What They Offer | ZX Control Advantage |
|-----------------|-----------------|----------------------|
| Udemy courses (ABC Automacao, Typebot+WPP) | Video lessons, student configures manually over days/weeks | Setup done in 1 hour, zero manual configuration, AI does everything |
| SaaS platforms (SocialHub, Zarpon, Kommo) | Web dashboard, monthly subscription R$97-497/mês | Student OWNS the infra locally, no recurring cost (except Z-API fallback), full customization |
| Formacao Gestor de Automacao (Promovaweb) | Training program, teaches tools over months | Working system on Day 1, not training over months |
| No-code builders (Typebot, Botpress, ChatMaxima) | Drag-and-drop chatbot builder | Real AI agent with BANT methodology, not rule-based chatbot. Multi-provider AI, not locked to one platform. |
| DIY with Claude Code | Student figures it out alone | Curated, tested, production-grade templates from ZX LAB's own running systems. Not "figure it out" but "it works on Day 1." |

## Sources

- Reference product: `~/agente-ia-vendas/` (CLAUDE.md, setup scripts, templates) -- HIGH confidence
- ZX LAB production systems: `~/.zxlab-mission-control/` (rate limiter, dispatch log, monitor, heartbeat) -- HIGH confidence
- PROJECT.md requirements and constraints -- HIGH confidence
- [Wizard UI Pattern: When to Use It](https://www.eleken.co/blog-posts/wizard-ui-pattern-explained) -- MEDIUM confidence
- [Command Line Interface Guidelines](https://clig.dev/) -- MEDIUM confidence
- [WhatsApp Infoprodutor Curso Online 2026 - SocialHub](https://www.socialhub.pro/blog/whatsapp-infoprodutor-curso-online-2026/) -- MEDIUM confidence
- [Automacao WhatsApp Vendas Guia Completo 2026](https://www.socialhub.pro/blog/automacao-whatsapp-vendas-guia-completo/) -- MEDIUM confidence
- [ABC Automacao de Baixo Custo - Udemy](https://www.udemy.com/course/abc-automacao-de-baixo-custo-typebot-whatsapp/) -- LOW confidence (competitor reference only)
- [Formacao Gestor de Automacao - Promovaweb](https://formacao.promovaweb.com/gestor-automacao-whatsapp/) -- LOW confidence (competitor reference only)
- [Progressive Onboarding UX Guide](https://userguiding.com/blog/progressive-onboarding) -- MEDIUM confidence
- [Setup Wizard Best Practices](https://tumgazeteler.com/the-comprehensive-guide-to-setup-wizard/) -- MEDIUM confidence
