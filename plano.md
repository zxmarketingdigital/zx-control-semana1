# Plano — Área de Membros com Seletor Semana 1 / Semana 2

## Context

`~/projetos/zx-control-semana1/docs/area-membros.html` (1550 linhas, 68 KB) hoje é uma área de membros **linear** focada só na Semana 1: login → sidebar com Aulas + 10 etapas → painéis de passo-a-passo.

A Semana 2 está sendo planejada como **repositório independente** (`zxmarketingdigital/zx-control-semana2`, ainda não criado) com 8 etapas próprias voltadas a robustez/otimização/publicação (RTK, skills, guardião, Supabase+Auth, mini-CRM publicado no Cloudflare Pages). Detalhes em `~/.claude/plans/recursive-yawning-willow.md`.

Este PR atualiza **só a área de membros** para comportar as duas semanas lado-a-lado antes da Sem2 estar pronta:

- Tela inicial pós-login vira **seletor com 2 cards** (Sem1 / Sem2), sem trava, cada card mostrando **lista do que será instalado + benefício de cada item** para gerar interesse antes do clone.
- Cada semana tem sua própria sidebar + painéis de etapa independentes.
- Progresso salvo separadamente por semana no localStorage (preserva o estado atual dos alunos).
- Card da Sem2 já traz o passo-a-passo `gh repo clone ... && claude` funcional (ativa assim que o repo for publicado).

**Arquivo a editar:** `~/projetos/zx-control-semana1/docs/area-membros.html` (único arquivo). Preservar todas as modificações locais do Rafael.

---

## Decisões confirmadas

1. **Sem2**: visão geral completa + passo-a-passo `clone + claude` já funcional (repo será publicado depois).
2. **Pós-login**: sempre mostra o seletor de semana. Botão "← Trocar semana" no top nav volta ao seletor.
3. **Estado**: chaves separadas `zxcontrol_s1` (já existe, preservada) e `zxcontrol_s2` (nova). Login/student migra para `zxcontrol_auth` comum; fallback lê de `zxcontrol_s1` para não derrubar sessões ativas.

---

## Arquitetura da nova página

```
┌─ #loginScreen ─────────────────┐   (inalterado)
└────────────────────────────────┘
          ↓ login ok
┌─ #weekSelector ────────────────┐   NOVO
│  Top nav (logo + logout)       │
│  ┌──────────┐  ┌──────────┐    │
│  │ Semana 1 │  │ Semana 2 │    │
│  │ Fundação │  │ Robustez │    │
│  │ (cliques)│  │ (cliques)│    │
│  └──────────┘  └──────────┘    │
└────────────────────────────────┘
          ↓ clique em card
┌─ #membersArea ─────────────────┐
│  Top nav: [← Trocar semana]    │   ← botão novo
│  Sidebar: etapas da semana ativa│
│  Content: painéis da semana     │
└────────────────────────────────┘
```

Três telas top-level alternadas via `display`: `#loginScreen`, `#weekSelector`, `#membersArea`.

---

## Mudanças no HTML

### 1. Novo bloco `#weekSelector` (inserir entre `#loginScreen` e `#membersArea`, ~linha 593)

Dois cards lado-a-lado (grid responsivo). Cada card contém:

- **Header**: badge ("Semana 1" / "Semana 2"), título ("Fundação Operacional" / "Operação Robusta"), subtítulo curto.
- **Tese** (1-2 linhas): o que o aluno sai tendo ao final da semana.
- **Lista de benefícios** (`benefit-list`): 6 itens (Sem1) / 8 itens (Sem2), cada um com ícone + nome + benefício direto. Gera interesse.
- **Meta**: "~1 hora" / "~1h15".
- **CTA**: botão "Começar Semana X →" que chama `openWeek(1)` / `openWeek(2)`.
- **Badge de progresso**: se `zxcontrol_sN.completed.length > 0`, mostra "N/10 concluídas" para sinalizar retomada.

**Conteúdo dos cards** (gerado do plano `recursive-yawning-willow.md`):

**Semana 1 — Fundação Operacional** (~1h)
> Ao final: WhatsApp + Email conectados, agente IA respondendo leads, disparos programados rodando, monitor diário ativo.

Benefícios:
1. 📱 **WhatsApp conectado** — seu número respondendo leads via Evolution API (grátis) ou Z-API
2. 📧 **Email automatizado** — integração Resend com plano gratuito 3.000 emails/mês
3. 🤖 **Agente IA BANT** — qualifica leads automaticamente (OpenAI, Gemini ou Claude)
4. 👥 **Base de contatos** — importa sua lista e organiza em banco local
5. 🚀 **Disparos seguros** — rate limiter (30/h, 150/dia) e dry-run obrigatório
6. 📊 **Monitor diário** — relatório de saúde às 8h, sem você precisar lembrar

**Semana 2 — Operação Robusta** (~1h15)
> Ao final: sua operação vira profissional — economiza 60-90% em tokens, se monitora sozinha, roda na nuvem e você publica seu primeiro mini-CRM online.

Benefícios:
1. 🎯 **Mission Control** — painel único com tudo da sua operação num HTML que você abre no browser
2. 💰 **RTK Token Killer** — 60-90% menos tokens Claude Code em operações repetitivas
3. 🛠 **Pack de skills pro** — `/status`, `/healthcheck`, `/fix`, `/dedup`, `/preflight`, `/harvest`, `/encerrar`
4. 🛡 **Agente Guardião + Heartbeat** — detecta queda e te avisa no WhatsApp em minutos
5. ☁️ **Supabase + Auth** — banco de dados na nuvem com login pronto, grátis
6. 📦 **Contatos na nuvem** — migra sua base da Sem1 (ou cola CSV) direto pro Supabase
7. 🌐 **Mini-CRM publicado** — deploy real no Cloudflare Pages com login, listagem e CRUD
8. ✅ **Checklist final** — Mission Control populado com links e status de cada módulo

**Nota de pré-requisito na Sem2** (não bloqueia): "Independente da Semana 1 — se pulou a Sem1, o setup cria o ambiente mínimo automaticamente."

### 2. Top nav do `#membersArea` — adicionar botão "Trocar semana"

No `.nav-brand` (linha ~600), inserir antes do ícone atual:

```html
<button class="btn-switch-week" onclick="backToSelector()">← Trocar semana</button>
```

Atualizar `.nav-brand-sub` dinamicamente: `Semana 1 — Setup Operação IA` ou `Semana 2 — Operação Robusta` conforme `activeWeek`.

### 3. Sidebar — renderizar etapas da semana ativa

`buildSidebar()` passa a ler `ETAPAS_S1` ou `ETAPAS_S2` conforme `activeWeek`. Header do sidebar troca "de 10" para "de N" dinamicamente.

### 4. Painéis de etapa da Semana 2

Criar 9 novos panels (`#panel-s2-0` Aulas + `#panel-s2-1..8`) após os panels existentes da Sem1, usando a mesma estrutura visual (`etapa-header`, `step-list`, `code-block`, `etapa-footer` com `btn-complete`).

Cada panel Sem2 precisa:
- **Etapa 0 (Aulas)** — placeholder: "Aulas Semana 2 em breve" + CTA "Começar setup → Etapa 1".
- **Etapa 1 (Primeiro acesso Sem2)** — comando `gh repo clone zxmarketingdigital/zx-control-semana2 ~/zx-control-semana2 && cd ~/zx-control-semana2 && claude`, passos idênticos à Etapa 2 da Sem1, e comando do Claude: `INICIAR SETUP SEMANA 2`.
- **Etapas 2-8** — cada uma com: bloco "O que é · Para que serve · Como usar no dia-a-dia" (padrão definido no plano Sem2) + `btn-complete` sem código executável. Conteúdo vem direto das 8 etapas do plano `recursive-yawning-willow.md`.

Para evitar colisão de IDs com a Sem1 (`panel-1`, `complete-1`, `status-1`), prefixar: `panel-s2-1`, `complete-s2-1`, `status-s2-1`. Sem1 mantém os IDs atuais (`panel-1`, `complete-1`...) para não quebrar.

### 5. Painéis da Sem1 — ajuste mínimo no Panel 0 (Aulas)

Adicionar acima das 3 aulas existentes um bloco "O que você vai construir nesta semana" reaproveitando a mesma lista de 6 benefícios do card seletor, para manter consistência e gerar contexto ao aluno antes das aulas.

Mesmo tratamento no Panel 0 da Sem2 (lista de 8 benefícios).

### 6. CSS novo

Adicionar seção `/* ═ WEEK SELECTOR ═ */` com:

- `#weekSelector` — min-height: 100vh, flex column, hidden por default.
- `.selector-top` — top nav mínimo (logo + nome + logout).
- `.selector-wrap` — container centralizado, max-width 1100px.
- `.selector-title` — heading "Escolha por onde começar".
- `.selector-sub` — "Sem trava. Você decide a ordem."
- `.week-grid` — `grid-template-columns: repeat(auto-fit, minmax(420px, 1fr))`, gap 24px.
- `.week-card` — estilo igual aos `.login-card` (bg3, border, radius 20px, padding 36px, hover elevação/border purple).
- `.week-card-badge` — jetbrains mono, purple.
- `.week-card-title` — 1.6rem, bold.
- `.benefit-list` — flex column, gap 10px.
- `.benefit-item` — ícone (emoji) + texto, 0.88rem.
- `.week-card-cta` — mesmo estilo do `.btn-login`.
- `.week-card-progress` — badge canto sup direito se tiver progresso.
- `.btn-switch-week` — botão discreto no top nav (text-style, hover purple).
- Responsivo: abaixo de 768px, cards empilham (`grid-template-columns: 1fr`).

### 7. JavaScript — refatoração do state e navegação

```js
// Novas constantes
const ETAPAS_S1 = [ ...ETAPAS atual... ]  // preserva
const ETAPAS_S2 = [
  { id: 0, title: 'Aulas Semana 2' },
  { id: 1, title: 'Primeiro Acesso' },
  { id: 2, title: 'Mission Control' },
  { id: 3, title: 'RTK Token Killer' },
  { id: 4, title: 'Skills Profissionais' },
  { id: 5, title: 'Guardião + Heartbeat' },
  { id: 6, title: 'Supabase + Auth' },
  { id: 7, title: 'Importar Contatos' },
  { id: 8, title: 'Mini-CRM Publicado' },
]

let activeWeek = 1  // definido ao entrar na semana

// State separado por semana (preserva zxcontrol_s1 existente)
function stateKey() { return `zxcontrol_s${activeWeek}` }
function authKey()  { return 'zxcontrol_auth' }
function getState()  { return JSON.parse(localStorage.getItem(stateKey()) || '{}') }
function saveState(s){ localStorage.setItem(stateKey(), JSON.stringify(s)) }
function getAuth()   { /* lê zxcontrol_auth; fallback pra zxcontrol_s1 p/ migração */ }
function saveAuth(a) { localStorage.setItem(authKey(), JSON.stringify(a)) }
```

Novas funções:
- `showSelector()` — esconde login e membersArea, mostra `#weekSelector`, atualiza badges de progresso de cada card lendo `zxcontrol_s1` e `zxcontrol_s2`.
- `openWeek(n)` — seta `activeWeek = n`, esconde selector, mostra `#membersArea`, chama `buildSidebar()` + `goToEtapa(getCurrentEtapa())`.
- `backToSelector()` — salva estado atual, esconde membersArea, volta a `showSelector()`.

Ajustes nas funções existentes (`buildSidebar`, `goToEtapa`, `markComplete`, `updateProgress`):
- Ler `ETAPAS_S1` ou `ETAPAS_S2` conforme `activeWeek`.
- Prefixar IDs dos elementos com `s${activeWeek}` (ex: `panel-s2-1`, `complete-s2-1`). Sem1 continua com IDs sem prefixo para manter compat — função helper `panelId(id)` retorna `activeWeek === 1 ? `panel-${id}` : `panel-s2-${id}``.
- `updateProgress()` usa `ETAPAS_Sx.length - 1` como denominador (exclui Aulas).
- Auto-avanço em `markComplete` usa comprimento da semana ativa.

Ajuste no `handleLogin` (linha ~1340): após salvar auth, chama `showSelector()` em vez de `openMembersArea()`.

Ajuste no `DOMContentLoaded` (linha ~1521): se auth salvo, chama `showSelector()`; restaurar botões completos dos dois state-keys.

---

## Arquivos críticos

| Ação | Arquivo |
|---|---|
| Editar | `~/projetos/zx-control-semana1/docs/area-membros.html` (único) |
| Referência (read-only) | `~/.claude/plans/recursive-yawning-willow.md` (fonte do conteúdo Sem2) |
| Referência (read-only) | `~/projetos/zx-control-semana1/CLAUDE.md` (etapas Sem1) |

---

## Verificação end-to-end

1. **Preview local**: abrir `area-membros.html` direto no browser (`file://`) — login continua funcionando via fetch à Supabase Edge Function `check-zxcontrol-access`.
2. **Login + seletor**: logar com credencial válida → deve aparecer `#weekSelector` com os 2 cards, cada um com 6/8 benefícios listados e CTA.
3. **Cards sem progresso**: primeira visita — cada card sem badge de progresso.
4. **Abrir Sem1**: clicar no card Sem1 → `#membersArea` aparece, sidebar mostra 10 etapas + Aulas, conteúdo intacto, top nav exibe "Semana 1 — Setup Operação IA" e botão "← Trocar semana".
5. **Progresso Sem1 preservado**: alunos com `zxcontrol_s1` salvo veem etapas marcadas como concluídas (chave não foi migrada).
6. **Trocar semana**: clicar "← Trocar semana" → volta ao `#weekSelector`, badge "X/10 concluídas" aparece no card Sem1.
7. **Abrir Sem2**: clicar card Sem2 → sidebar mostra 8 etapas + Aulas, painel Aulas mostra "em breve", Etapa 1 traz comando `gh repo clone zxmarketingdigital/zx-control-semana2 && claude`.
8. **Marcar Sem2 completo**: completar uma etapa na Sem2 → `localStorage.zxcontrol_s2` atualiza, `zxcontrol_s1` intacto.
9. **Reload preservando**: reload de página → volta para `#weekSelector` (não pula direto pra última semana).
10. **Logout**: limpa `zxcontrol_auth`, preserva progresso das duas semanas.
11. **Mobile**: viewport 375px — cards do seletor empilham, sidebar da semana continua funcionando.
12. **Checar IDs duplicados**: grep no HTML final para garantir que `id="panel-1"` etc. não colidem entre Sem1 e Sem2 (Sem2 usa prefixo `s2-`).
13. **Deploy dual**: após aprovação, seguir padrão DUAL ZX Control (Cloudflare Pages + Worker path) — fora do escopo deste plano, será feito em passo separado.
