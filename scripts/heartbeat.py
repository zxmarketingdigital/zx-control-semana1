#!/usr/bin/env python3
"""
Heartbeat em 3 camadas da Semana 2.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from week2_lib import HEARTBEAT_DIR, ensure_week2_structure, latest_heartbeat_snapshot, load_config, now_iso

TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
if TEMPLATES_DIR.exists():
    sys.path.insert(0, str(TEMPLATES_DIR))

from dispatch_log_template import log_dispatch, should_send
from rate_limiter_template import ZAPIRateLimiter
from whatsapp_api_template import send_whatsapp

import monitor


def write_snapshot(layer_name, payload):
    ensure_week2_structure()
    path = HEARTBEAT_DIR / f"{layer_name}.json"
    payload["layer"] = layer_name
    payload["updated_at"] = now_iso()
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def parse_iso(value):
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


def is_recent(timestamp, max_age_minutes):
    if not timestamp:
        return False
    dt = parse_iso(timestamp)
    if not dt:
        return False
    delta = datetime.now() - dt
    return delta.total_seconds() <= max_age_minutes * 60


def send_alert(config, title, lines):
    student_phone = config.get("student_phone", "")
    if not student_phone:
        return False, "student_phone nao configurado"

    message = "\n".join([title, ""] + lines)
    if not should_send(student_phone, message, window_hours=2):
        return False, "alerta duplicado"

    limiter = ZAPIRateLimiter()
    if not limiter.can_send(student_phone):
        return False, "rate limiter bloqueou"

    try:
        ok = send_whatsapp(student_phone, message, config)
    except Exception as exc:
        return False, f"falha no envio: {exc}"

    if ok:
        limiter.record_send(student_phone)
        log_dispatch(student_phone, message, "week2-heartbeat-alert")
        return True, "enviado"
    return False, "envio retornou false"


def run_watchdog(config):
    report = monitor.generate_report(config)
    failing = [item for item in report["checks"] if not item["ok"]]
    snapshot = {
        "status": "ok" if not failing else "degraded",
        "checks": report["checks"],
        "failing_services": [item["service"] for item in failing],
    }
    return write_snapshot("watchdog", snapshot)


def run_heartbeat(config):
    snapshots = latest_heartbeat_snapshot()
    watchdog = snapshots.get("watchdog") or {}
    watchdog_fresh = is_recent(watchdog.get("updated_at"), 10)
    failing_services = watchdog.get("failing_services") or []
    status = "ok" if watchdog_fresh and not failing_services else "alert"
    path = write_snapshot(
        "heartbeat",
        {
            "status": status,
            "watchdog_fresh": watchdog_fresh,
            "failing_services": failing_services,
        },
    )
    if status != "ok":
        send_alert(
            config,
            "⚠️ Heartbeat detectou instabilidade",
            [
                f"Watchdog recente: {'sim' if watchdog_fresh else 'nao'}",
                f"Servicos falhando: {', '.join(failing_services) if failing_services else 'nenhum snapshot valido'}",
            ],
        )
    return path


def run_last_resort(config):
    snapshots = latest_heartbeat_snapshot()
    heartbeat = snapshots.get("heartbeat") or {}
    heartbeat_fresh = is_recent(heartbeat.get("updated_at"), 20)
    heartbeat_ok = heartbeat.get("status") == "ok"
    status = "ok" if heartbeat_fresh and heartbeat_ok else "critical"
    path = write_snapshot(
        "last_resort",
        {
            "status": status,
            "heartbeat_fresh": heartbeat_fresh,
            "heartbeat_status": heartbeat.get("status", "missing"),
        },
    )
    if status != "ok":
        send_alert(
            config,
            "🚨 Last resort acionado",
            [
                f"Heartbeat recente: {'sim' if heartbeat_fresh else 'nao'}",
                f"Status heartbeat: {heartbeat.get('status', 'missing')}",
                "Verifique monitor, agente e conexoes principais.",
            ],
        )
    return path


def main():
    parser = argparse.ArgumentParser(description="Heartbeat em 3 camadas")
    parser.add_argument("--layer", choices=["watchdog", "heartbeat", "last_resort", "all"], default="all")
    args = parser.parse_args()

    config = load_config()
    created = []
    if args.layer in {"watchdog", "all"}:
        created.append(run_watchdog(config))
    if args.layer in {"heartbeat", "all"}:
        created.append(run_heartbeat(config))
    if args.layer in {"last_resort", "all"}:
        created.append(run_last_resort(config))

    for path in created:
        print(f"Snapshot atualizado: {path}")


if __name__ == "__main__":
    main()
