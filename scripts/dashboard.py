#!/usr/bin/env python3
"""
Dashboard HTML local da Semana 2.
"""

import argparse
import json
import sqlite3
import sys
from html import escape
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from week2_lib import (
    DASHBOARD_DIR,
    SALES_DB,
    ensure_week2_structure,
    latest_dashboard_path,
    latest_heartbeat_snapshot,
    load_checkpoint,
    load_config,
    now_iso,
)

import monitor


def latest_sales(limit=8):
    if not SALES_DB.exists():
        return []
    conn = sqlite3.connect(str(SALES_DB))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT platform, external_id, sale_status, product_name,
                   buyer_name, buyer_email, amount_cents, currency, received_at
            FROM sales_events
            ORDER BY received_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def find_latest_status_html():
    logs_dir = Path.home() / ".operacao-ia" / "logs"
    files = sorted(logs_dir.glob("status_*.html"))
    return files[-1] if files else None


def badge(ok):
    return "ok" if ok else "error"


def money(amount_cents, currency):
    amount = (amount_cents or 0) / 100
    return f"{currency} {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def build_html(config, report, sales, checkpoint, heartbeat):
    checks_html = []
    for item in report["checks"]:
        checks_html.append(
            f"""
            <div class="card mini">
              <div class="eyebrow">{escape(item['service'])}</div>
              <div class="status {badge(item['ok'])}">{'Operando' if item['ok'] else 'Atenção'}</div>
              <p>{escape(item['details'])}</p>
            </div>
            """
        )

    sales_rows = []
    for sale in sales:
        buyer = sale["buyer_name"] or sale["buyer_email"] or "Cliente"
        sales_rows.append(
            "<tr>"
            f"<td>{escape(sale['platform'])}</td>"
            f"<td>{escape(buyer)}</td>"
            f"<td>{escape(sale['product_name'] or '-')}</td>"
            f"<td>{escape(sale['sale_status'] or '-')}</td>"
            f"<td>{escape(money(sale['amount_cents'], sale['currency'] or 'BRL'))}</td>"
            f"<td>{escape(sale['received_at'])}</td>"
            "</tr>"
        )
    if not sales_rows:
        sales_rows.append("<tr><td colspan='6'>Nenhuma venda recebida ainda.</td></tr>")

    checkpoint_items = []
    for name, item in checkpoint.get("steps", {}).items():
        checkpoint_items.append(
            f"<li><strong>{escape(name)}</strong> <span>{escape(item.get('status', '-'))}</span></li>"
        )
    if not checkpoint_items:
        checkpoint_items.append("<li>Nenhum checkpoint salvo ainda.</li>")

    heartbeat_items = []
    for layer_name, snapshot in heartbeat.items():
        if not snapshot:
            heartbeat_items.append(f"<li><strong>{layer_name}</strong> <span>sem snapshot</span></li>")
            continue
        heartbeat_items.append(
            f"<li><strong>{layer_name}</strong> <span>{escape(snapshot.get('status', 'unknown'))} em {escape(snapshot.get('updated_at', '-'))}</span></li>"
        )

    latest_status = find_latest_status_html()
    latest_status_link = latest_status.name if latest_status else "nenhum"

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ZX Control Dashboard</title>
  <style>
    :root {{
      --bg: #f4efe7;
      --ink: #1c1917;
      --muted: #6b645d;
      --panel: #fffdf8;
      --line: #ddd2c2;
      --accent: #b45309;
      --accent-2: #0f766e;
      --danger: #b91c1c;
      --glow: radial-gradient(circle at top left, rgba(180,83,9,0.16), transparent 36%);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.75), rgba(244,239,231,0.95)),
        var(--glow),
        var(--bg);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 56px; }}
    .hero {{
      display: grid;
      grid-template-columns: 1.4fr 1fr;
      gap: 18px;
      margin-bottom: 18px;
    }}
    .card {{
      background: rgba(255,253,248,0.88);
      border: 1px solid var(--line);
      border-radius: 22px;
      padding: 22px;
      box-shadow: 0 12px 40px rgba(28,25,23,0.06);
      backdrop-filter: blur(10px);
    }}
    .card h1, .card h2 {{ margin: 0 0 10px; line-height: 1.05; }}
    .eyebrow {{
      font-family: "Courier New", monospace;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .hero h1 {{ font-size: clamp(36px, 5vw, 62px); }}
    .hero p, p {{ color: var(--muted); }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .mini-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .mini .status {{
      display: inline-block;
      margin-bottom: 8px;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
    }}
    .status.ok {{ background: rgba(15,118,110,0.12); color: var(--accent-2); }}
    .status.error {{ background: rgba(185,28,28,0.1); color: var(--danger); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 12px 8px; border-bottom: 1px solid var(--line); font-size: 14px; }}
    ul {{ margin: 0; padding-left: 18px; }}
    li {{ margin-bottom: 8px; }}
    .pill {{
      display: inline-block;
      padding: 6px 10px;
      border-radius: 999px;
      background: rgba(180,83,9,0.1);
      color: var(--accent);
      font-size: 12px;
      font-weight: 700;
      margin-right: 8px;
      margin-bottom: 8px;
    }}
    a {{ color: var(--accent); }}
    @media (max-width: 900px) {{
      .hero, .grid, .mini-grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <article class="card">
        <div class="eyebrow">Semana 2</div>
        <h1>Operação visual, conectada e retomável.</h1>
        <p>Aluno: <strong>{escape(config.get('student_name', '-'))}</strong> | Negócio: <strong>{escape(config.get('business_name', '-'))}</strong></p>
        <p>Atualizado em {escape(now_iso())}. O dashboard consolida saúde da operação, vendas recebidas, heartbeat e checkpoint do setup da semana 2.</p>
        <div>
          <span class="pill">WhatsApp: {escape(config.get('whatsapp_provider', '-'))}</span>
          <span class="pill">IA: {escape(config.get('ai_provider', '-'))}</span>
          <span class="pill">Webhook port: {escape(str(config.get('week2', {}).get('webhook_port', 8782)))}</span>
          <span class="pill">Dashboard port: {escape(str(config.get('week2', {}).get('dashboard_port', 8783)))}</span>
        </div>
      </article>
      <article class="card">
        <div class="eyebrow">Atalhos</div>
        <p>Último status HTML da semana 1: <strong>{escape(latest_status_link)}</strong></p>
        <p>Dashboard local: <code>~/.operacao-ia/dashboard/index.html</code></p>
        <p>Webhooks:</p>
        <p><code>/webhook/hotmart</code>, <code>/webhook/greenn</code>, <code>/webhook/kiwify</code></p>
      </article>
    </section>

    <section class="card" style="margin-bottom: 18px;">
      <div class="eyebrow">Saúde Atual</div>
      <div class="mini-grid">
        {''.join(checks_html)}
      </div>
    </section>

    <section class="grid">
      <article class="card">
        <div class="eyebrow">Vendas Capturadas</div>
        <h2>Últimos eventos</h2>
        <table>
          <thead>
            <tr>
              <th>Plataforma</th>
              <th>Cliente</th>
              <th>Produto</th>
              <th>Status</th>
              <th>Valor</th>
              <th>Recebido em</th>
            </tr>
          </thead>
          <tbody>
            {''.join(sales_rows)}
          </tbody>
        </table>
      </article>

      <article class="card">
        <div class="eyebrow">Heartbeat 3 Camadas</div>
        <h2>Snapshots</h2>
        <ul>{''.join(heartbeat_items)}</ul>
        <div class="eyebrow" style="margin-top: 18px;">Checkpoint / Resume</div>
        <ul>{''.join(checkpoint_items)}</ul>
      </article>
    </section>
  </div>
</body>
</html>"""


def build_dashboard():
    ensure_week2_structure()
    try:
        config = load_config()
        report = monitor.generate_report(config)
    except FileNotFoundError:
        config = {
            "student_name": "Demo",
            "business_name": "ZX Control",
            "whatsapp_provider": "pending",
            "ai_provider": "pending",
            "week2": {"webhook_port": 8782, "dashboard_port": 8783},
        }
        report = {
            "checks": [
                {"service": "whatsapp", "ok": False, "details": "config.json ainda nao foi criado"},
                {"service": "email", "ok": False, "details": "rode a Semana 1 antes da operacao real"},
                {"service": "agent", "ok": False, "details": "ambiente demo"},
            ]
        }
    sales = latest_sales()
    checkpoint = load_checkpoint()
    heartbeat = latest_heartbeat_snapshot()
    html = build_html(config, report, sales, checkpoint, heartbeat)
    output_path = latest_dashboard_path()
    output_path.write_text(html, encoding="utf-8")
    return output_path


class DashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return


def serve_dashboard(port):
    build_dashboard()
    handler = lambda *args, **kwargs: DashboardHandler(*args, directory=str(DASHBOARD_DIR), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"Dashboard servindo em http://127.0.0.1:{port}")
    server.serve_forever()


def main():
    parser = argparse.ArgumentParser(description="Dashboard local da semana 2")
    parser.add_argument("--build", action="store_true", help="Gera o HTML e sai")
    parser.add_argument("--serve", action="store_true", help="Serve o dashboard localmente")
    parser.add_argument("--port", type=int, default=8783)
    args = parser.parse_args()

    if args.serve:
      serve_dashboard(args.port)
      return

    output = build_dashboard()
    print(f"Dashboard gerado em: {output}")


if __name__ == "__main__":
    main()
