# Roadmap: ZX Control — Semana 1: Setup Operacao IA

## Overview

Do `git clone && cd && claude` ate uma operacao de automacao com IA funcionando em ~1 hora. Quatro fases entregam: fundacao do setup guiado (Phase 1), conectividade WhatsApp + Email (Phase 2), automacoes core com agente IA e disparos (Phase 3), e operacoes de monitoramento com validacao final (Phase 4).

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Conductor CLAUDE.md, pre-requisitos, estrutura de pastas e CLAUDE.md personalizado
- [ ] **Phase 2: Connectivity** - WhatsApp (Evolution/Z-API) + Email (Resend) + rate limiter + SQLite abstractions
- [ ] **Phase 3: Automation Core** - Agente IA WhatsApp, disparos agendados, importacao de contatos
- [ ] **Phase 4: Operations** - Monitor, bom dia, status matinal, validacao end-to-end

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
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Connectivity
**Goal**: O aluno tem WhatsApp e Email conectados, protegidos por rate limiter e dispatch log, prontos para enviar mensagens
**Depends on**: Phase 1
**Requirements**: WPP-01, WPP-02, WPP-03, WPP-04, EML-01, EML-02, DAT-02, DAT-03
**Success Criteria** (what must be TRUE):
  1. WhatsApp esta conectado via QR Code (Evolution ou Z-API) com estado validado
  2. Email esta configurado via Resend e um email de teste foi recebido com sucesso
  3. Todo envio WhatsApp passa pelo rate limiter (30/h, 150/dia, 90s entre msgs) sem excecao
  4. Dispatch log com deduplicacao impede envio duplicado da mesma mensagem ao mesmo destinatario
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

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
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Operations
**Goal**: O aluno tem monitoramento automatico, status matinal no WhatsApp e validacao end-to-end confirmando que tudo funciona
**Depends on**: Phase 3
**Requirements**: OPS-01, OPS-03, OPS-04, OPS-05, VAL-01, VAL-02
**Success Criteria** (what must be TRUE):
  1. O monitor verifica saude do WhatsApp e Email a cada 5 minutos e alerta o aluno quando algo falha
  2. Uma mensagem de "bom dia" configuravel e enviada automaticamente todo dia via WhatsApp
  3. O status matinal chega no WhatsApp do aluno com o estado de todos os servicos da operacao
  4. A validacao end-to-end ao final do setup confirma todas as integracoes e envia status no WhatsApp do aluno
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/0 | Not started | - |
| 2. Connectivity | 0/0 | Not started | - |
| 3. Automation Core | 0/0 | Not started | - |
| 4. Operations | 0/0 | Not started | - |
