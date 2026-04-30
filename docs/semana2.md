# ZX Control — Semana 2

## O que entra nesta etapa

- Dashboard HTML local com visão consolidada da operação
- Webhooks de vendas para Hotmart, Greenn e Kiwify
- Heartbeat em 3 camadas
- Checkpoint/resume para continuar um setup interrompido

## Como rodar

```bash
python3 setup/setup_week2.py
```

O setup da semana 2:

1. Copia os scripts novos para `~/.operacao-ia/scripts/`
2. Salva a configuração em `~/.operacao-ia/config/config.json`
3. Gera `~/.operacao-ia/config/week2_checkpoint.json`
4. Sobe o servidor local de webhooks e o dashboard, se você confirmar

## Endpoints criados

- `http://127.0.0.1:8782/webhook/hotmart`
- `http://127.0.0.1:8782/webhook/greenn`
- `http://127.0.0.1:8782/webhook/kiwify`
- `http://127.0.0.1:8782/health`

## Dashboard

- Arquivo gerado em `~/.operacao-ia/dashboard/index.html`
- Servidor local padrão em `http://127.0.0.1:8783`

## Scripts principais

- `~/.operacao-ia/scripts/sales_webhooks.py`
- `~/.operacao-ia/scripts/dashboard.py`
- `~/.operacao-ia/scripts/heartbeat.py`
- `~/.operacao-ia/scripts/start_week2_stack.sh`

## Heartbeat 3 camadas

- `watchdog`: usa a checagem atual da operação
- `heartbeat`: valida se o watchdog está atualizando e se houve falhas
- `last_resort`: dispara alerta quando a camada intermediária para ou degrada

Os snapshots ficam em:

- `~/.operacao-ia/logs/heartbeat/watchdog.json`
- `~/.operacao-ia/logs/heartbeat/heartbeat.json`
- `~/.operacao-ia/logs/heartbeat/last_resort.json`
