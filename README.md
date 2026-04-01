# ZX Control — Semana 1: Setup Operação IA

> Repositório exclusivo para alunos do ZX Control.
> Ao final desta sessão você terá WhatsApp + Email conectados, um agente IA respondendo leads e disparos programados funcionando — sem digitar um único comando.

---

## O que você vai ter no final

| O que | Detalhe |
|-------|---------|
| WhatsApp conectado | Evolution API local (gratuita) como padrão, com Z-API como fallback opcional |
| Email configurado | Resend — 3.000 envios/mês grátis |
| Agente IA de vendas | Responde leads automaticamente via WhatsApp (OpenAI / Gemini / Anthropic) |
| Disparos programados | WhatsApp + Email para sua lista de contatos |
| Rate limiter ativo | Proteção anti-bloqueio (30 msgs/hora, 90s entre envios) |
| Monitor rodando | Avisa no seu WhatsApp se algo cair |
| Status matinal | Relatório diário automático no seu WhatsApp |

---

## Como começar

```bash
git clone [link-do-repo] zx-control-semana1
cd zx-control-semana1
claude
```

O Claude lê as instruções e conduz você por tudo — sem precisar digitar mais nada.

---

## Requisitos mínimos

| Requisito | Versão mínima | Como instalar |
|-----------|--------------|---------------|
| Python | 3.10+ | Ver `docs/prerequisitos.md` |
| Node.js | 18+ | Ver `docs/prerequisitos.md` |
| Git | qualquer recente | Ver `docs/prerequisitos.md` |
| Docker | 20+ | Ver `docs/prerequisitos.md` |

> **Evolution API é o padrão do produto.**
> **8GB RAM** é o mínimo recomendado para rodar bem.
> **16GB+ RAM** é o ideal para maior estabilidade.
> **Z-API** fica como fallback opcional, não como fluxo principal.

---

## O que está incluído em cada semana

| Funcionalidade | Semana 1 | Semana 2+ |
|----------------|:--------:|:---------:|
| Verificação de pré-requisitos | ✅ | — |
| Pasta `~/.operacao-ia/` configurada | ✅ | — |
| WhatsApp conectado (Evolution padrão + fallback Z-API) | ✅ | — |
| Email (Resend) configurado | ✅ | — |
| Agente IA WhatsApp (BANT, multi-provider) | ✅ | — |
| Disparos programados WhatsApp | ✅ | — |
| Disparos programados Email | ✅ | — |
| Importação de contatos (CSV, texto) | ✅ | — |
| Rate limiter anti-bloqueio | ✅ | — |
| Monitor básico WhatsApp + Email | ✅ | — |
| Status matinal automático | ✅ | — |
| Dashboard HTML visual | — | ✅ |
| Integração Hotmart / Greenn / Kiwify | — | ✅ |
| Onboarding automático pós-venda | — | ✅ |
| Heartbeat 3 camadas | — | ✅ |
| Copy com IA (geração automática) | — | ✅ Semana 3 |
| CRM com IA | — | ✅ Semana 4 |

---

## Estrutura do repositório

```
zx-control-semana1/
├── CLAUDE.md               # Instrutor automático — Claude lê e executa
├── README.md               # Este arquivo
├── setup/
│   ├── check_prerequisites.py   # Verifica Python, Node, Git, Docker
│   ├── setup_environment.py     # Cria ~/.operacao-ia/ e config inicial
│   ├── install_evolution.py     # Instala Evolution API local
│   ├── connect_whatsapp.py      # Conecta o WhatsApp via QR Code
│   ├── setup_zapi.py            # Fallback opcional Z-API
│   ├── setup_email.py           # Configura Resend e envia teste
│   ├── setup_agent.py           # Configura o agente IA BANT
│   ├── import_contacts.py       # Importa contatos por texto ou CSV
│   ├── setup_dispatcher.py      # Prepara o dispatcher de disparos
│   └── setup_monitor.py         # Ativa o monitor diario
├── scripts/
│   ├── agent_bant.py            # Fonte do agente deployado em ~/.operacao-ia/scripts/
│   ├── dispatcher.py            # Fonte do dispatcher deployado
│   └── monitor.py               # Fonte do monitor deployado
├── templates/
│   ├── claude_md_template.md    # Template para CLAUDE.md personalizado do aluno
│   ├── rate_limiter_template.py # Rate limiter local em SQLite
│   ├── dispatch_log_template.py # Deduplicacao de disparos em SQLite
│   └── whatsapp_api_template.py # Abstracao Evolution vs Z-API
└── docs/
    └── prerequisitos.md         # Guia de instalação por sistema operacional
```

---

## Precisa de ajuda?

Acesse o grupo do ZX Control e mencione o problema — ou abra uma issue neste repositório.
