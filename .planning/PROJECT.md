# ZX Control — Semana 1: Setup Operação IA

## What This Is

Repositório guiado (padrão `git clone && cd && claude`) que conduz alunos do ZX Control do zero até uma operação de automação com IA funcionando — WhatsApp + Email + Agente IA + Monitor — em ~1 hora, sem precisar saber programar. O Claude lê o CLAUDE.md e executa todo o setup automaticamente, perguntando apenas dados do negócio do aluno.

## Core Value

O aluno termina a primeira sessão com automações FUNCIONANDO no WhatsApp e Email dele — disparos programados, agente IA respondendo leads, e um monitor que avisa se algo cair. O "wow moment" é ver funcionando no mesmo dia.

## Requirements

### Validated (Phase 1-4, 2026-04-01)

- [x] Setup guiado por Claude: CLAUDE.md conduz 10 etapas sem o aluno digitar comandos
- [x] Verificação de pré-requisitos (Python 3.10+, Node 18+, Git, Docker)
- [x] Instalação automática da Evolution API (WhatsApp local, preferência) com fallback Z-API
- [x] Conexão WhatsApp via QR Code com validação de estado
- [x] Configuração de email (Resend API) com envio de teste
- [x] Estrutura de pastas `~/.operacao-ia/` com logs, config, scripts, dados
- [x] Importação de contatos: aluno cola/escreve ou fornece documento (CSV, texto)
- [x] Rate limiter global WhatsApp (proteção anti-bloqueio: 30/h, 150/dia, 90s)
- [x] Dispatch log com deduplicação (SQLite, previne envio duplicado)
- [x] Monitor básico: health check WhatsApp + Email, relatório HTML diário
- [x] Agente IA WhatsApp: bot BANT respondendo leads com multi-turno, multi-provider (OpenAI/Gemini/Anthropic)
- [x] Status matinal automático: relatório diário no WhatsApp do aluno (LaunchAgent 8h)
- [x] Teste end-to-end ao final do setup: valida todas as integrações e envia status
- [x] Disparos programados WhatsApp com dispatcher + enviar.sh + dry-run

### Active

- [ ] Bom dia automático (WhatsApp) — mensagem diária configurável (template existe, precisa de script dedicado)
- [ ] Disparos programados Email para lista do aluno (dispatcher suporta WhatsApp, email ainda manual)
- [ ] Geração de CLAUDE.md personalizado com regras do negócio do aluno (setup usa CLAUDE.md fixo do repo)

### Out of Scope

- Integração com plataformas de vendas (Hotmart, Greenn, Kiwify) — Semana 2
- Dashboard HTML visual — Semana 2
- Heartbeat 3 camadas — Semana 2
- Copy com IA (geração automática) — Semana 3
- Follow-up equipe automatizado — Semana 3
- Email marketing em massa com tracking — Semana 3
- CRM com IA — Semana 4 (bonus)
- Onboarding automático pós-venda — Semana 2+
- Skills system (comandos /vendas, /status) — Semana 4
- Google Sheets sync — complexidade desnecessária para v1

## Context

### Produto
- **ZX Control**: Mentoria de 30 dias, R$997/12x97 via Greenn
- **Turma 1**: Iniciou 01/Abr/2026
- **Público**: Infoprodutores, agências, consultores — muitos NÃO vendem online, usam WhatsApp/email para qualquer tipo de comunicação comercial
- **Grupo turma**: ZX CONTROL (ID Z-API: 120363424694288167-group)

### Referência de implementação
- **agente-ia-vendas** (`~/agente-ia-vendas/`): Repo público GitHub com padrão CLAUDE.md auto-executor + setup/ + templates/ — modelo exato a replicar
- **Mission Control** (`~/.zxlab-mission-control/`): Sistema produção ZX LAB com todos os scripts que serão templated (rate limiter, dispatch log, monitor, heartbeat, dashboard)
- **Templates prontos**: agent_template.py, watcher_template.py, sessions_template.py, agent_core_template.py — multi-provider IA, SQLite sessions, BANT prompt generation

### Stack aluno
- Python 3.10+ (scripts de automação)
- Evolution API local via Docker (WhatsApp) — preferência por ser gratuito
- Z-API como fallback (pago R$97/mês, mais leve, para quem tem 8GB RAM)
- Resend (email gratuito 3.000/mês)
- SQLite (dados locais: contatos, sessões, dispatch log)
- Claude Code CLI (interface do aluno)
- cron/LaunchAgent (agendamento macOS/Linux)

### Lista de contatos
- Aluno escreve direto, cola texto, ou fornece arquivo (CSV, TXT)
- Setup parseia e importa para SQLite local
- Não precisa de banco externo na Semana 1

## Constraints

- **RAM**: Alunos com 8GB devem usar Z-API (Evolution precisa 16GB+)
- **Zero código**: Aluno NUNCA precisa editar código — Claude faz tudo
- **1 hora**: Setup completo deve ser factível em ~1h para quem já tem pré-requisitos
- **Repo privado**: Acesso apenas para alunos matriculados (GitHub invite)
- **macOS + Linux**: Suporte completo. Windows via WSL2.
- **Anti-bloqueio**: Todo disparo WhatsApp DEVE passar pelo rate limiter (30/h, 150/dia, 90s entre msgs)
- **Independência**: Agente IA roda separado dos disparos — mesma instância Evolution, sem conflito

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Evolution API como preferência sobre Z-API | Gratuito, local, sem custo mensal para aluno | Validado — Evolution é default, Z-API fallback |
| Agente IA incluído na Semana 1 | Prometido aos alunos, é o maior wow moment | Validado — funciona com OpenAI/Gemini/Anthropic |
| Disparos flexíveis (não só alerta de venda) | Maioria dos alunos não vende online — precisam de infra de comunicação genérica | Validado — dispatcher aceita mensagem livre |
| Contatos via input direto (sem Sheets/Supabase) | Mínima fricção no Day 1, sem dependência externa | Validado — inline + CSV, SQLite local |
| Repo privado GitHub | Conteúdo exclusivo da mentoria, não público como agente-ia-vendas | Validado |
| Status matinal via WhatsApp | Aluno vê que tudo funciona todo dia sem abrir terminal | Validado — LaunchAgent 8h + relatório HTML |
| Manter agente-ia-vendas como código integrado (não clone separado) | Evita complexidade de 2 repos no Day 1, mas herda templates testados | Validado — templates copiados para ~/.operacao-ia/ |
| Setup aguarda "INICIAR SETUP" do aluno | Evita setup automático assustando aluno não-técnico | Validado — commit 48f1b56 |
| User-Agent obrigatório em todas as chamadas HTTP | Cloudflare bloqueia requests sem User-Agent (Resend, Z-API) | Validado — descoberto em teste real |
| Detecção de credenciais existentes | Alunos ZX LAB já têm Z-API/Resend configurados em ~/.zxlab-mission-control/.env | Validado — reutiliza sem redigitar |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-01 after Phase 1-4 completion + hardening pass*
