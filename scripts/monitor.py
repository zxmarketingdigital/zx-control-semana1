#!/usr/bin/env python3
"""
Monitor de saude da Operacao IA.
Este arquivo e a fonte do script deployado em ~/.operacao-ia/scripts/monitor.py.
"""

import argparse
import html
import json
import subprocess
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
sys.path.insert(0, str(SCRIPT_DIR))
if TEMPLATES_DIR.exists():
    sys.path.insert(0, str(TEMPLATES_DIR))

from dispatch_log_template import log_dispatch, should_send
from rate_limiter_template import ZAPIRateLimiter
from whatsapp_api_template import send_whatsapp


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
LOGS_DIR = BASE_DIR / "logs"
PLIST_LABEL = "br.zxlab.operacao-ia.monitor"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_LABEL}.plist"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def save_config(config):
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def http_json(url, headers=None, method="GET", timeout=15):
    request = urllib.request.Request(url, headers=headers or {}, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return response.status, json.loads(body) if body else {}


def check_evolution(config):
    evolution = config.get("evolution", {})
    base_url = evolution.get("base_url", "http://localhost:8080").rstrip("/")
    api_key = evolution.get("api_key", "")
    instance = evolution.get("instance_name", "operacao-ia")
    status = {"service": "evolution", "ok": False, "details": ""}

    try:
        _, health = http_json(f"{base_url}/health")
        _, state = http_json(
            f"{base_url}/instance/connectionState/{instance}",
            headers={"apikey": api_key},
        )
        conn_state = state.get("state") or state.get("instance", {}).get("state", "")
        status["ok"] = conn_state == "open"
        status["details"] = f"health={health.get('status', 'ok')} state={conn_state or 'desconhecido'}"
    except Exception as exc:
        status["details"] = str(exc)

    return status


def check_zapi(config):
    endpoint = config.get("zapi", {}).get("status_url", "")
    status = {"service": "zapi", "ok": False, "details": ""}
    if not endpoint:
        status["details"] = "status_url nao configurada"
        return status

    try:
        _, payload = http_json(endpoint)
        connected = payload.get("connected", False) or payload.get("smartphoneConnected", False)
        status["ok"] = bool(connected)
        status["details"] = json.dumps(payload, ensure_ascii=False)[:180]
    except Exception as exc:
        status["details"] = str(exc)
    return status


def check_resend(config):
    email = config.get("email", {})
    api_key = email.get("api_key", "")
    status = {"service": "resend", "ok": False, "details": ""}
    if not api_key:
        status["details"] = "api_key nao configurada"
        return status

    try:
        _, payload = http_json(
            "https://api.resend.com/domains",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        status["ok"] = True
        status["details"] = f"dominios={len(payload.get('data', []))}"
    except Exception as exc:
        status["details"] = str(exc)
    return status


def check_agent_process():
    status = {"service": "agent", "ok": False, "details": ""}
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        running = "agent_bant.py" in result.stdout
        status["ok"] = running
        status["details"] = "processo rodando" if running else "processo nao encontrado"
    except Exception as exc:
        status["details"] = str(exc)
    return status


def build_html(report):
    rows = []
    for item in report["checks"]:
        badge = "OK" if item["ok"] else "ERRO"
        rows.append(
            "<tr>"
            f"<td>{html.escape(item['service'])}</td>"
            f"<td>{badge}</td>"
            f"<td>{html.escape(item['details'])}</td>"
            "</tr>"
        )

    return (
        "<html><head><meta charset='utf-8'><title>Status Operacao IA</title>"
        "<style>body{font-family:Arial,sans-serif;padding:24px;}table{border-collapse:collapse;width:100%;}"
        "td,th{border:1px solid #ddd;padding:8px;text-align:left;}th{background:#f4f4f4;}</style>"
        "</head><body>"
        f"<h1>Status Operacao IA - {html.escape(report['generated_at'])}</h1>"
        "<table><tr><th>Servico</th><th>Status</th><th>Detalhes</th></tr>"
        + "".join(rows)
        + "</table></body></html>"
    )


def status_file_path():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    return LOGS_DIR / f"status_{date.today().isoformat()}.html"


def build_whatsapp_summary(report):
    lines = ["📊 Status da Operacao IA", ""]
    for item in report["checks"]:
        lines.append(f"{'✅' if item['ok'] else '❌'} {item['service']}: {item['details']}")
    return "\n".join(lines)


def send_summary_if_possible(config, message):
    student_phone = config.get("student_phone", "")
    if not student_phone:
        return False, "student_phone nao configurado"

    limiter = ZAPIRateLimiter()
    if not should_send(student_phone, message, window_hours=6):
        return False, "resumo ja enviado recentemente"
    if not limiter.can_send(student_phone):
        return False, "rate limiter bloqueou envio"

    try:
        ok = send_whatsapp(student_phone, message, config)
    except Exception as exc:
        return False, f"falha no envio: {exc}"

    if ok:
        limiter.record_send(student_phone)
        log_dispatch(student_phone, message, "monitor-status")
        return True, "enviado"
    return False, "falha no envio"


def generate_report(config):
    checks = []
    if config.get("whatsapp_provider") == "evolution":
        checks.append(check_evolution(config))
    else:
        checks.append(check_zapi(config))
    checks.append(check_resend(config))
    checks.append(check_agent_process())

    report = {
        "generated_at": datetime.now().isoformat(),
        "checks": checks,
    }
    return report


def install_launchagent():
    plist = ET.Element("plist", version="1.0")
    job = ET.SubElement(plist, "dict")

    def add_key_value(parent, key, value):
        ET.SubElement(parent, "key").text = key
        if isinstance(value, list):
            array = ET.SubElement(parent, "array")
            for item in value:
                ET.SubElement(array, "string").text = item
        elif isinstance(value, int):
            ET.SubElement(parent, "integer").text = str(value)
        else:
            ET.SubElement(parent, "string").text = value

    add_key_value(job, "Label", PLIST_LABEL)
    add_key_value(job, "ProgramArguments", [sys.executable, str(Path(__file__).resolve()), "--now"])
    ET.SubElement(job, "key").text = "RunAtLoad"
    ET.SubElement(job, "false")
    ET.SubElement(job, "key").text = "StartCalendarInterval"
    schedule = ET.SubElement(job, "dict")
    add_key_value(schedule, "Hour", 8)
    add_key_value(schedule, "Minute", 0)
    add_key_value(job, "StandardOutPath", str(LOGS_DIR / "monitor.log"))
    add_key_value(job, "StandardErrorPath", str(LOGS_DIR / "monitor.error.log"))
    add_key_value(job, "WorkingDirectory", str(BASE_DIR))

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        + ET.tostring(plist, encoding="unicode")
    )
    PLIST_PATH.write_text(content, encoding="utf-8")

    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True, check=False)
    subprocess.run(["launchctl", "load", str(PLIST_PATH)], capture_output=True, check=False)


def uninstall_launchagent():
    subprocess.run(["launchctl", "unload", str(PLIST_PATH)], capture_output=True, check=False)
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()


def main():
    parser = argparse.ArgumentParser(description="Monitor da Operacao IA")
    parser.add_argument("--now", action="store_true", help="Roda o health check agora")
    parser.add_argument("--install-launchagent", action="store_true")
    parser.add_argument("--uninstall-launchagent", action="store_true")
    args = parser.parse_args()

    if args.install_launchagent:
        install_launchagent()
        print(f"LaunchAgent instalado: {PLIST_PATH}")
        return

    if args.uninstall_launchagent:
        uninstall_launchagent()
        print("LaunchAgent removido.")
        return

    config = load_config()
    report = generate_report(config)
    html_content = build_html(report)
    html_path = status_file_path()
    html_path.write_text(html_content, encoding="utf-8")

    summary = build_whatsapp_summary(report)
    sent, detail = send_summary_if_possible(config, summary)
    report["whatsapp_summary"] = {"sent": sent, "detail": detail}

    print(f"Relatorio HTML: {html_path}")
    for item in report["checks"]:
        print(f"{'OK' if item['ok'] else 'ERRO'} {item['service']}: {item['details']}")
    print(f"WhatsApp resumo: {detail}")


if __name__ == "__main__":
    main()
