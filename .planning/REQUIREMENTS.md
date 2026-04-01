# Requirements: ZX Control — Semana 1: Setup Operação IA

**Defined:** 2026-04-01
**Core Value:** O aluno termina a primeira sessão com automações FUNCIONANDO no WhatsApp e Email dele — disparos programados, agente IA respondendo leads, e um monitor que avisa se algo cair.

## v1 Requirements

### Setup Experience

- [ ] **SET-01**: O repositório inicia o setup guiado via `CLAUDE.md` imediatamente após `git clone && cd && claude`, sem exigir que o aluno digite comandos operacionais.
- [ ] **SET-02**: O fluxo guiado usa linguagem simples em PT-BR, sem jargão técnico, compreensível por não-técnicos.
- [ ] **SET-03**: O setup completo dura aproximadamente 1 hora para alunos que já atendem os pré-requisitos.
- [ ] **SET-04**: O setup gera um ambiente operacional personalizado em `~/.operacao-ia/` (config, scripts, dados, logs).

### Pré-requisitos e Plataforma

- [ ] **PRE-01**: O setup verifica Python 3.10+, Node 18+, Git e Docker antes de prosseguir.
- [ ] **PRE-02**: A solução suporta macOS e Linux diretamente, e Windows via WSL2.
- [ ] **PRE-03**: O setup seleciona ou recomenda o provedor WhatsApp baseado nas capacidades da máquina (especialmente RAM).

### WhatsApp

- [ ] **WPP-01**: O sistema instala e configura a Evolution API automaticamente como provedor WhatsApp preferencial (máquinas com 16GB+ RAM).
- [ ] **WPP-02**: O sistema suporta Z-API como provedor WhatsApp de fallback (máquinas com 8GB RAM).
- [ ] **WPP-03**: O sistema conecta WhatsApp via QR Code e valida o estado da conexão antes de avançar.
- [ ] **WPP-04**: Todos os envios WhatsApp passam por um rate limiter global anti-bloqueio (30/hora, 150/dia, 90s mínimo entre mensagens).
- [ ] **WPP-05**: Os disparos WhatsApp suportam casos de uso flexíveis de comunicação comercial (follow-up, conteúdo, vendas), não apenas alertas de venda.

### Email

- [ ] **EML-01**: O sistema configura envio de email via Resend durante o setup.
- [ ] **EML-02**: O setup envia e verifica um email de teste antes de marcar email como pronto.
- [ ] **EML-03**: O sistema suporta disparos de email agendados para a base de contatos do aluno.

### Dados e Configuração

- [ ] **DAT-01**: O sistema cria estrutura de pastas local em `~/.operacao-ia/` (config, scripts, dados, logs).
- [ ] **DAT-02**: O sistema armazena dados operacionais localmente usando SQLite.
- [ ] **DAT-03**: O sistema mantém dispatch log com deduplicação para prevenir envios duplicados.
- [ ] **DAT-04**: O sistema importa contatos a partir de texto colado, digitado ou arquivo (CSV/TXT).

### Agente IA

- [ ] **AIA-01**: O sistema provisiona um agente IA no WhatsApp já na Semana 1.
- [ ] **AIA-02**: O agente suporta conversas multi-turno com leads usando lógica BANT.
- [ ] **AIA-03**: O agente suporta múltiplos provedores de IA: OpenAI, Gemini e Anthropic.
- [ ] **AIA-04**: O runtime do agente permanece operacionalmente independente dos disparos agendados, compartilhando a mesma instância WhatsApp com segurança.

### Agendamento e Monitoramento

- [ ] **OPS-01**: O sistema suporta uma mensagem diária configurável de "bom dia" via WhatsApp.
- [ ] **OPS-02**: O sistema suporta disparos agendados de WhatsApp para a base de contatos importada.
- [ ] **OPS-03**: O sistema executa um monitor básico a cada 5 minutos verificando saúde do WhatsApp e email.
- [ ] **OPS-04**: O sistema alerta quando serviços monitorados falham.
- [ ] **OPS-05**: O sistema envia um relatório de status matinal automático no WhatsApp do aluno com o estado geral da operação.

### Validação e Handoff

- [ ] **VAL-01**: O setup executa validação end-to-end ao final do fluxo.
- [ ] **VAL-02**: A validação final confirma integrações e envia mensagem de status no WhatsApp do aluno.
- [ ] **VAL-03**: O setup gera um `CLAUDE.md` personalizado com contexto do negócio do aluno e regras operacionais.

## v2 Requirements

### Semana 2+

- **SEM2-01**: Integração com plataformas de vendas (Hotmart, Greenn, Kiwify) — webhook de venda
- **SEM2-02**: Dashboard HTML visual com status de tudo
- **SEM2-03**: Heartbeat 3 camadas (watchdog 5min → heartbeat 15min → last resort 30min)
- **SEM2-04**: Checkpoint/resume para setup interrompido
- **SEM3-01**: Copy com IA (Gemini/Claude gera copy diariamente)
- **SEM3-02**: Follow-up automático de equipe
- **SEM3-03**: Email marketing em massa com tracking
- **SEM4-01**: CRM com IA
- **SEM4-02**: Skills system (/vendas, /status, /recover)
- **SEM4-03**: Onboarding automático pós-venda

## Out of Scope

| Feature | Reason |
|---------|--------|
| Google Sheets sync | Complexidade desnecessária Day 1 — SQLite é suficiente |
| Integrações de venda (Hotmart/Greenn/Kiwify) | Semana 2 |
| Dashboard HTML | Semana 2 |
| Copy gerada por IA | Semana 3 |
| CRM com IA | Semana 4 (bonus) |
| Skills system | Semana 4 |
| Suporte a Windows nativo | WSL2 cobre, nativo é complexo demais |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SET-01 | Phase 1 | Pending |
| SET-02 | Phase 1 | Pending |
| SET-03 | Phase 1 | Pending |
| SET-04 | Phase 1 | Pending |
| PRE-01 | Phase 1 | Pending |
| PRE-02 | Phase 1 | Pending |
| PRE-03 | Phase 1 | Pending |
| WPP-01 | Phase 2 | Pending |
| WPP-02 | Phase 2 | Pending |
| WPP-03 | Phase 2 | Pending |
| WPP-04 | Phase 2 | Pending |
| WPP-05 | Phase 3 | Pending |
| EML-01 | Phase 2 | Pending |
| EML-02 | Phase 2 | Pending |
| EML-03 | Phase 3 | Pending |
| DAT-01 | Phase 1 | Pending |
| DAT-02 | Phase 2 | Pending |
| DAT-03 | Phase 2 | Pending |
| DAT-04 | Phase 3 | Pending |
| AIA-01 | Phase 3 | Pending |
| AIA-02 | Phase 3 | Pending |
| AIA-03 | Phase 3 | Pending |
| AIA-04 | Phase 3 | Pending |
| OPS-01 | Phase 4 | Pending |
| OPS-02 | Phase 3 | Pending |
| OPS-03 | Phase 4 | Pending |
| OPS-04 | Phase 4 | Pending |
| OPS-05 | Phase 4 | Pending |
| VAL-01 | Phase 4 | Pending |
| VAL-02 | Phase 4 | Pending |
| VAL-03 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-01*
*Last updated: 2026-04-01 after initial definition*
