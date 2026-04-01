# ZX Control Semana 1 — Session Handoff

Data: 2026-04-01
Repo: `~/projetos/zx-control-semana1/`
Branch: `main`
Estado atual: repo limpo, pronto para continuar

## Objetivo do projeto
- Produto guiado por repositório: aluno faz `git clone && cd && claude`
- O `CLAUDE.md` conduz toda a configuração sem o aluno editar código
- Output operacional do aluno vai para `~/.operacao-ia/`

## Escopo implementado

### Phase 1
- `setup/check_prerequisites.py`
- `setup/setup_environment.py`
- `templates/claude_md_template.md`
- `docs/prerequisitos.md`
- `README.md`

Commit de referência:
- `3655725`

### Phase 2 — Connectivity
- `setup/install_evolution.py`
- `setup/connect_whatsapp.py`
- `setup/setup_zapi.py`
- `setup/setup_email.py`
- `templates/rate_limiter_template.py`
- `templates/dispatch_log_template.py`
- `templates/whatsapp_api_template.py`
- `CLAUDE.md` atualizado com Etapas 3 e 4

Commit:
- `976c638` — `feat: phase 2 — connectivity (whatsapp + email + rate limiter)`

### Phase 3 — Agente IA + Disparos + Monitor
- `scripts/agent_bant.py`
- `scripts/dispatcher.py`
- `scripts/monitor.py`
- `setup/setup_agent.py`
- `setup/import_contacts.py`
- `setup/setup_dispatcher.py`
- `setup/setup_monitor.py`
- `CLAUDE.md` atualizado com Etapas 6-10

Commit:
- `f1b76ce` — `feat: phase 3 — agente IA BANT + dispatcher + monitor (etapas 6-10)`

## Correções feitas depois da implementação inicial

### Hardening funcional
Commit:
- `b9799c8` — `fix: harden phase 3 agent startup and contact tagging`

Incluiu:
- agente BANT com rate limiter + dispatch log nas respostas
- polling funcional para Evolution
- deduplicação melhor no fluxo Z-API
- suporte real a tags na importação de contatos
- setup do agente agora inicia o processo

### Resiliência validada por smoke test
Commit:
- `49f15d9` — `fix: improve phase 3 smoke-test resilience`

Incluiu:
- fallback de import dos templates para scripts no repo
- monitor não quebra mais se envio de WhatsApp falhar
- dispatcher gera relatórios com microssegundos para evitar overwrite
- importação manual conta linhas inválidas corretamente

### UX de onboarding e entrega
Commit:
- `29ceccc` — `fix: improve onboarding ux and setup guidance`

Incluiu:
- Etapa 5 do `CLAUDE.md` alinhada com continuação automática
- Etapa 10 do `CLAUDE.md` agora fecha com mensagem final completa
- prompts de `setup_email.py` e `setup_agent.py` agora repromptam em vez de abortar
- `setup_monitor.py` valida melhor `student_phone`
- `README.md` atualizado para refletir o estado real do repo

## Estado atual dos arquivos principais
- `CLAUDE.md` cobre Etapas 1-10
- `README.md` está alinhado com Phase 1, 2 e 3
- scripts-fonte de deploy vivem em `scripts/`
- setup scripts vivem em `setup/`
- templates auxiliares vivem em `templates/`

## Regras e decisões que devem ser mantidas
- `~/.operacao-ia/` é o único destino dos artefatos do aluno
- WhatsApp:
  - `ram_gb >= 16` -> `evolution`
  - `ram_gb < 16` -> `zapi`
- Email: Resend
- Agente IA: BANT multi-provider
- OpenAI usa `gpt-5.4-mini` com `max_completion_tokens`
- Todo envio WhatsApp passa por rate limiter + dispatch log
- Agente IA e dispatcher são processos separados
- Aluno nunca edita código manualmente

## Validações já feitas
- `python3 -m py_compile` passou para todos os `.py` em `setup/`, `scripts/` e `templates/`
- smoke tests locais em `HOME=/tmp/zxcontrol-smoke/home` validaram:
  - importação de contatos
  - `dispatcher.py --dry-run`
  - filtro por tag
  - geração de relatórios sem overwrite
  - `monitor.py --now` gerando HTML sem cair com traceback em falha de rede

## O que ainda falta validar para entrega
- fluxo fim a fim real em máquina limpa sem `~/.operacao-ia/` prévio
- teste real com Evolution API
- teste real com Z-API
- teste real com Resend
- teste real do agente respondendo uma conversa
- teste real do dispatcher com 1 contato
- teste real do LaunchAgent do monitor no macOS

## Melhor próximo passo em outra sessão
1. Fazer homologação real de ponta a ponta
2. Registrar o resultado em um checklist de QA
3. Ajustar qualquer detalhe operacional encontrado

## Comando útil para retomar
Ao abrir outra sessão do Claude Code, use algo como:

```text
Leia docs/session-handoff-2026-04-01.md e continue a homologação final do ZX Control Semana 1.
```
