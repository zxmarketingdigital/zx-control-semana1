#!/usr/bin/env python3
"""
Dispatcher flexivel de disparos WhatsApp.
Este arquivo e a fonte do script deployado em ~/.operacao-ia/scripts/dispatcher.py.
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from dispatch_log_template import log_dispatch, should_send
from rate_limiter_template import ZAPIRateLimiter
from whatsapp_api_template import send_whatsapp


BASE_DIR = Path.home() / ".operacao-ia"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
CONTACTS_DB = BASE_DIR / "data" / "contacts.db"
LOGS_DIR = BASE_DIR / "logs"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def load_message(args):
    if args.message:
        return args.message.strip()
    if args.file:
        return Path(args.file).read_text(encoding="utf-8").strip()
    raise SystemExit("Forneca --message ou --file")


def connect_contacts_db():
    conn = sqlite3.connect(str(CONTACTS_DB))
    conn.row_factory = sqlite3.Row
    return conn


def fetch_contacts(tag=None):
    with connect_contacts_db() as conn:
        if tag:
            rows = conn.execute(
                "SELECT name, phone, tags FROM contacts WHERE tags LIKE ? ORDER BY name, phone",
                (f"%{tag}%",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT name, phone, tags FROM contacts ORDER BY name, phone"
            ).fetchall()
    return [dict(row) for row in rows]


def build_contacts_from_phones(raw_phones):
    contacts = []
    for raw in raw_phones or []:
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits:
            continue
        contacts.append({"name": digits, "phone": digits, "tags": ""})
    return contacts


def progress_bar(index, total):
    if total <= 0:
        return "[░░░░░░░░░░] 0%"
    pct = int((index / total) * 100)
    filled = min(10, int(round(pct / 10)))
    return f"[{'█' * filled}{'░' * (10 - filled)}] {pct}%"


def report_path():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOGS_DIR / f"dispatch_{timestamp}.json"


def build_report(message, contacts, dry_run, tag):
    return {
        "created_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "tag": tag or "",
        "message_preview": message[:280],
        "total_contacts": len(contacts),
        "results": [],
    }


def main():
    parser = argparse.ArgumentParser(description="Dispatcher de disparos WhatsApp")
    parser.add_argument("--message", help="Mensagem direta")
    parser.add_argument("--file", help="Arquivo .txt com a mensagem")
    parser.add_argument("--dry-run", action="store_true", help="Mostra preview sem enviar")
    parser.add_argument("--tag", help="Filtra contatos por tag")
    parser.add_argument("--phones", nargs="+", help="Lista direta de telefones")
    args = parser.parse_args()

    config = load_config()
    message = load_message(args)
    contacts = build_contacts_from_phones(args.phones) if args.phones else fetch_contacts(args.tag)
    limiter = ZAPIRateLimiter()
    report = build_report(message, contacts, args.dry_run, args.tag)

    if not contacts:
        raise SystemExit("Nenhum contato encontrado para o filtro informado.")

    total = len(contacts)
    print(f"Total de contatos: {total}")
    print(f"Dry-run: {'sim' if args.dry_run else 'nao'}")
    print()

    sent = 0
    skipped = 0
    failed = 0

    for index, contact in enumerate(contacts, start=1):
        name = contact.get("name") or "Contato"
        phone = contact.get("phone") or ""
        rendered = message.replace("{nome}", name)
        prefix = f"Enviando {index}/{total}... {progress_bar(index, total)}"

        result = {
            "name": name,
            "phone": phone,
            "status": "",
            "detail": "",
        }

        if not should_send(phone, rendered):
            result["status"] = "skipped"
            result["detail"] = "duplicado"
            skipped += 1
            print(f"{prefix} pulado (duplicado) -> {name}")
            report["results"].append(result)
            continue

        if not limiter.can_send(phone):
            result["status"] = "skipped"
            result["detail"] = "rate_limiter"
            skipped += 1
            print(f"{prefix} pulado (rate limiter) -> {name}")
            report["results"].append(result)
            continue

        if args.dry_run:
            result["status"] = "preview"
            result["detail"] = rendered[:200]
            print(f"{prefix} preview -> {name} ({phone})")
            report["results"].append(result)
            continue

        try:
            ok = send_whatsapp(phone, rendered, config)
            if ok:
                limiter.record_send(phone)
                log_dispatch(phone, rendered, "manual-dispatch")
                result["status"] = "sent"
                result["detail"] = "ok"
                sent += 1
                print(f"{prefix} ok -> {name}")
            else:
                result["status"] = "failed"
                result["detail"] = "envio_retornou_false"
                failed += 1
                print(f"{prefix} falhou -> {name}")
        except Exception as exc:
            result["status"] = "failed"
            result["detail"] = str(exc)
            failed += 1
            print(f"{prefix} erro -> {name}: {exc}")

        report["results"].append(result)

    report["summary"] = {
        "sent": sent,
        "skipped": skipped,
        "failed": failed,
        "dry_run": args.dry_run,
    }

    path = report_path()
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print()
    print(f"Relatorio salvo em: {path}")
    print(f"Resumo: {sent} enviados, {skipped} pulados, {failed} falhas")


if __name__ == "__main__":
    main()
