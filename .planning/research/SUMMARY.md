# Research Summary

## Objective

ZX Control Semana 1 deve entregar um setup guiado por Claude Code que leva um aluno não técnico, em cerca de 1 hora, de `git clone && cd && claude` até uma operação local de automação com IA funcionando: WhatsApp, email, agente IA, disparos agendados e monitoramento.

## Main Conclusions

### Product shape
- O produto não é um app tradicional; é um repositório-condutor.
- O `CLAUDE.md` é o orquestrador principal do setup e funciona como uma máquina de estados sequencial.
- O resultado do setup é um ambiente autônomo em `~/.operacao-ia/`, não uma dependência permanente do repositório.

### Recommended stack
- Python 3.10+ como runtime principal de automações, agent, monitor e scripts.
- Claude Code CLI como interface do aluno.
- Evolution API v2.2.0 como padrão para WhatsApp em máquinas com 16GB+ RAM.
- Z-API como fallback para máquinas com 8GB ou quando Docker/Evolution forem inviáveis.
- Resend para email por simplicidade operacional.
- SQLite para contatos, sessões, dispatch log e rate limiter.
- LaunchAgents no macOS e cron no Linux para agendamento persistente.

### Core architecture
- `CLAUDE.md` conduz o fluxo de setup passo a passo.
- Scripts de setup ficam no repo; scripts operacionais finais são gerados em `~/.operacao-ia/`.
- Templates com placeholders permitem personalização sem o aluno editar código.
- `whatsapp_api.py` abstrai Evolution vs Z-API.
- `rate_limiter.py` e `dispatch_log.py` são camadas obrigatórias para qualquer envio WhatsApp.
- Agente IA, disparos e monitor rodam desacoplados e compartilham apenas módulos comuns e SQLite.

### Most important features
- Setup auto-iniciado por Claude, sem o aluno digitar comandos.
- Check de pré-requisitos com linguagem simples.
- Conexão WhatsApp por QR Code com validação real de estado.
- Configuração de email com envio de teste.
- Importação flexível de contatos.
- Rate limiter global e deduplicação.
- Agente IA WhatsApp multi-provider com lógica BANT.
- Disparos agendados de WhatsApp e email.
- Bom dia automático, monitor a cada 5 minutos e status matinal.
- Teste end-to-end como encerramento do setup.

## Key Decisions

- Priorizar Evolution API como opção gratuita e local, com fallback explícito para Z-API.
- Manter Python como única linguagem operacional do aluno.
- Usar SQLite e estrutura local-first na Semana 1.
- Integrar o agente IA já na Semana 1 por ser o maior "wow moment".
- Suportar comunicação comercial genérica, não apenas alertas de venda.
- Manter o setup repo separado da operação gerada em `~/.operacao-ia/`.

## Critical Risks

- Docker/Evolution em Macs com 8GB degrada a máquina e quebra a experiência.
- Envio agressivo no WhatsApp pode banir o número do aluno.
- Setup parcial sem checkpoint/resume gera estados corrompidos.
- API keys inválidas sem validação imediata fazem o setup "parecer concluído" sem funcionar.
- Permissões do macOS podem bloquear cron, Docker e arquivos sem feedback claro.
- QR Code expirando e desconexão silenciosa do WhatsApp precisam de tratamento explícito.
- SQLite precisa de WAL, busy timeout e separação por responsabilidade para evitar lock.

## Build Priorities

1. Conductor `CLAUDE.md` e checks de pré-requisito.
2. Escolha de provedor WhatsApp e conexão por QR.
3. Configuração de email e teste.
4. Config base, abstrações, rate limiter e dispatch log.
5. Importação de contatos.
6. Templates do agente IA e dispatches.
7. Monitoramento e status matinal.
8. Geração final dos scripts, scheduler e teste end-to-end.

## Explicit Non-Goals For Semana 1

- Hotmart, Greenn e Kiwify.
- Dashboard HTML.
- Google Sheets sync.
- CRM com IA.
- Sistema de skills.
- Copy automática com IA.
- Heartbeat 3 camadas.
