# Roadmap: ZX Control — Semana 1: Setup Operacao IA

## Overview

Do `git clone && cd && claude` ate uma operacao de automacao com IA funcionando em ~1 hora. Quatro fases entregam: fundacao do setup guiado (Phase 1), conectividade WhatsApp + Email (Phase 2), automacoes core com agente IA e disparos (Phase 3), e operacoes de monitoramento com validacao final (Phase 4).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Conductor CLAUDE.md, pre-requisitos, estrutura de pastas e CLAUDE.md personalizado
- [x] **Phase 2: Connectivity** - WhatsApp (Evolution/Z-API) + Email (Resend) + rate limiter + SQLite abstractions
- [x] **Phase 3: Automation Core** - Agente IA WhatsApp, disparos agendados, importacao de contatos
- [x] **Phase 4: Operations** - Monitor, bom dia, status matinal, validacao end-to-end

## Phase Details

### Phase 1: Foundation
**Goal**: O aluno executa `git clone && cd && claude` e o Claude conduz o setup sem comandos manuais, verificando pre-requisitos e criando a estrutura operacional
**Depends on**: Nothing (first phase)
**Requirements**: SET-01, SET-02, SET-03, SET-04, PRE-01, PRE-02, PRE-03, DAT-01, VAL-03
**Success Criteria** (what must be TRUE):
  1. Ao abrir o repo com Claude, o setup inicia automaticamente em PT-BR sem o aluno digitar comandos operacionais
  2. O setup verifica Python 3.10+, Node 18+, Git e Docker e comunica resultado em linguagem simples
  3. A estrutura `~/.operacao-ia/` (config, scripts, dados, logs) existe e esta populada com config base
  4. O setup recomenda Evolution ou Z-API baseado na RAM da maquina do aluno
  5. Um CLAUDE.md personalizado com regras do negocio do aluno esta gerado e funcional
**Plans**: Completed

Plans:
- [x] 01-01: CLAUDE.md conductor com boas-vindas e fluxo de 10 etapas
- [x] 01-02: check_prerequisites.py + setup_environment.py + estrutura ~/.operacao-ia/

**Completed**: 2026-04-01 (commit 3655725)
**Post-delivery fixes**: Busca Python em paths alternativos (~/.local/bin/, pyenv, homebrew) — commit 9b9c838

### Phase 2: Connectivity
**Goal**: O aluno tem WhatsApp e Email conectados, protegidos por rate limiter e dispatch log, prontos para enviar mensagens
**Depends on**: Phase 1
**Requirements**: WPP-01, WPP-02, WPP-03, WPP-04, EML-01, EML-02, DAT-02, DAT-03
**Success Criteria** (what must be TRUE):
  1. WhatsApp esta conectado via QR Code (Evolution ou Z-API) com estado validado
  2. Email esta configurado via Resend e um email de teste foi recebido com sucesso
  3. Todo envio WhatsApp passa pelo rate limiter (30/h, 150/dia, 90s entre msgs) sem excecao
  4. Dispatch log com deduplicacao impede envio duplicado da mesma mensagem ao mesmo destinatario
**Plans**: Completed

Plans:
- [x] 02-01: setup_zapi.py + install_evolution.py + connect_whatsapp.py
- [x] 02-02: setup_email.py (Resend) + rate_limiter_template.py + dispatch_log_template.py

**Completed**: 2026-04-01 (commit 976c638)
**Post-delivery fixes**: User-Agent em todas as chamadas HTTP, detecção de credenciais existentes, regex de email, client_token no config — commit 9b9c838

### Phase 3: Automation Core
**Goal**: O aluno tem um agente IA respondendo leads no WhatsApp, contatos importados e disparos agendados funcionando
**Depends on**: Phase 2
**Requirements**: WPP-05, EML-03, DAT-04, AIA-01, AIA-02, AIA-03, AIA-04, OPS-02
**Success Criteria** (what must be TRUE):
  1. O agente IA responde mensagens de leads no WhatsApp com conversas multi-turno usando logica BANT
  2. O agente suporta pelo menos 2 provedores de IA (OpenAI, Gemini ou Anthropic) configurados pelo aluno
  3. Contatos importados (texto colado, digitado ou CSV/TXT) estao no SQLite e disponiveis para disparos
  4. Disparos agendados de WhatsApp e Email para a base de contatos funcionam via cron/LaunchAgent
  5. O agente IA roda independente dos disparos, compartilhando a mesma instancia WhatsApp sem conflito
**Plans**: Completed

Plans:
- [x] 03-01: setup_agent.py (OpenAI/Gemini/Anthropic) + agent_bant.py + start_agent.sh
- [x] 03-02: import_contacts.py + setup_dispatcher.py + dispatcher.py + enviar.sh

**Completed**: 2026-04-01 (commit f1b76ce)
**Post-delivery fixes**: Modelo gpt-5.4-mini → gpt-4o-mini, sinônimos de tom, EOFError em import_contacts — commit 9b9c838

### Phase 4: Operations
**Goal**: O aluno tem monitoramento automatico, status matinal no WhatsApp e validacao end-to-end confirmando que tudo funciona
**Depends on**: Phase 3
**Requirements**: OPS-01, OPS-03, OPS-04, OPS-05, VAL-01, VAL-02
**Success Criteria** (what must be TRUE):
  1. O monitor verifica saude do WhatsApp e Email a cada 5 minutos e alerta o aluno quando algo falha
  2. Uma mensagem de "bom dia" configuravel e enviada automaticamente todo dia via WhatsApp
  3. O status matinal chega no WhatsApp do aluno com o estado de todos os servicos da operacao
  4. A validacao end-to-end ao final do setup confirma todas as integracoes e envia status no WhatsApp do aluno
**Plans**: Completed

Plans:
- [x] 04-01: setup_monitor.py + monitor.py (health check WhatsApp/Email/Agent) + LaunchAgent 8h
- [x] 04-02: Relatório HTML diário + envio de resumo via WhatsApp + validação end-to-end

**Completed**: 2026-04-01 (commit f1b76ce)
**Post-delivery fixes**: User-Agent + Client-Token no monitor, phase_completed tracking, sys.executable — commit 9b9c838

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 2/2 | Complete | 2026-04-01 |
| 2. Connectivity | 2/2 | Complete | 2026-04-01 |
| 3. Automation Core | 2/2 | Complete | 2026-04-01 |
| 4. Operations | 2/2 | Complete | 2026-04-01 |

## Post-Delivery: Hardening (2026-04-01)

Teste real com aluno (Rafael/ZX LAB) revelou 12 problemas de UX e resiliência. Todos corrigidos no commit 9b9c838:

**Bloqueadores corrigidos:** Python detection em paths alternativos, modelo OpenAI inexistente, regex de email, User-Agent em chamadas HTTP, Client-Token no monitor Z-API.

**Alta prioridade:** Detecção de credenciais existentes no setup_zapi, schema do config.json consistente entre scripts, EOFError handling, phase_completed no monitor.

**Média prioridade:** Mensagem de RAM "0GB", sinônimos de tom do agente, sys.executable propagado.
