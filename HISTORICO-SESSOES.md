# Histórico de Sessões — zx-control-semana1

> Registro do que foi feito a cada sessão de trabalho neste projeto (mais recente no topo).
> Mantido pelo `/encerrar` via `zx-worklog.py`. Ler no início pra recuperar contexto.

---

## 2026-08-13 — Fix Gemini aposentado (404)

**Feito:** Mesmo defeito do gemini-2.5-flash/2.0-flash aposentado encontrado e corrigido nos 4 repos irmaos da linha de nicho + no setup Semana 1, apos achar na Clinica Cheia (aluno Diogo reportou).
**Fix:** modelo default trocado p/ alias gemini-flash-lite-latest, GEMINI_MODEL opcional com trim+fallback, parser resiliente a part sem text e a thought:true (raciocinio interno).
**Arquivos:** src/gemini/client.ts (contabilidade, corretor) · src/config.ts+src/ia.ts (juridico) · scripts/agent_bant.py+setup/setup_agent.py (semana1) · setup/configure.mjs+setup/smoke.mjs (corretor).
**Deploy:** push origin/main nos 4 (CI verde: 101/164/84 testes). Cascas geradoras (~/.claude/skills/criar-repo-setup-colaborador/templates/) corrigidas junto p/ setup novo nao nascer quebrado; regra registrada na SKILL.md.
**Pendencias:** nenhuma. Aviso enviado no grupo ZX Control 5 com instrucao de git pull + wrangler deploy.

## 2026-07-27 — Players ScaleUp → Bunny + Curso Base de 12 para 10 aulas

**Feito (1):** as 3 aulas do Módulo 1 serviam iframes ScaleUp que pararam de tocar — a conta ScaleUp morreu (backend devolve playlists/undefined). Os 3 vídeos já estavam no Bunny desde 09/Jul, então foi só trocar o embed: 2733b728→e37b50c5, 1b9b080f→0a02b4e1, d91c373b→cdcf6cf6. Smoke test baixou 3s de vídeo real de cada playlist HLS (5 renditions).

**Feito (2):** Curso Base tinha 12 aulas, mas as aulas 10 ('Boas práticas — revisão masterclass') e 11 ('Sessão especial Semana Santa') embutiam exatamente o MESMO vídeo das aulas 3 e 8 (0729a0ff e afa1f569). Os painéis só tinham título+subtítulo+iframe, sem instrução própria — nada de conteúdo se perdeu. Removidos panel-base-10/11 e as entradas em ETAPAS_BASE; display do Módulo 2 reajustado (aula 12 de display 5 → 3). Ids NÃO renumerados.

**Nota:** turma é immutable no zxcontrol-versoes.json, mas Rafael aprovou — trocar player é infra, e sem a troca as aulas ficariam inacessíveis quando o ScaleUp for cancelado.

**Arquivos:** docs/index.html
**Deploy:** wrangler pages deploy docs --project-name=zx-control-semana1; produção com 10 painéis base e zero ScaleUp.
**Pendências:** nenhuma.

## 2026-07-08 — Mapa inicial do projeto (backfill)

**Feito:** MAPA-PROJETO.md via mapear-projeto.

