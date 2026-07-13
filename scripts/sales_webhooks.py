#!/usr/bin/env python3
"""
Servidor local de webhooks para Hotmart, Greenn e Kiwify.
"""

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from week2_lib import connect_sales_db, ensure_week2_structure, load_config, now_iso

TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
if TEMPLATES_DIR.exists():
    sys.path.insert(0, str(TEMPLATES_DIR))

from dispatch_log_template import log_dispatch, should_send
from rate_limiter_template import ZAPIRateLimiter
from whatsapp_api_template import send_whatsapp


def digits_only(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def extract_first(payload, paths, default=""):
    for path in paths:
        current = payload
        ok = True
        for key in path:
            if not isinstance(current, dict) or key not in current:
                ok = False
                break
            current = current[key]
        if ok and current not in (None, ""):
            return current
    return default


def as_cents(value):
    try:
        if value in (None, ""):
            return 0
        if isinstance(value, str):
            value = value.replace(".", "").replace(",", ".")
        return int(round(float(value) * 100))
    except Exception:
        return 0


def normalize_payload(platform, payload):
    if platform == "hotmart":
        return {
            "external_id": str(
                extract_first(
                    payload,
                    [
                        ("data", "purchase", "transaction"),
                        ("purchase", "transaction"),
                        ("id",),
                    ],
                )
            ),
            "sale_status": str(extract_first(payload, [("event",), ("data", "purchase", "status"), ("status",)], "received")),
            "product_name": str(extract_first(payload, [("data", "product", "name"), ("product", "name")], "Produto Hotmart")),
            "buyer_name": str(extract_first(payload, [("data", "buyer", "name"), ("buyer", "name")])),
            "buyer_email": str(extract_first(payload, [("data", "buyer", "email"), ("buyer", "email")])),
            "buyer_phone": digits_only(extract_first(payload, [("data", "buyer", "checkout_phone"), ("buyer", "phone")])),
            "amount_cents": as_cents(extract_first(payload, [("data", "purchase", "price", "value"), ("purchase", "price", "value"), ("value",)], 0)),
            "currency": str(extract_first(payload, [("data", "purchase", "price", "currency_code"), ("currency",)], "BRL")),
        }

    if platform == "greenn":
        return {
            "external_id": str(extract_first(payload, [("sale", "code"), ("code",), ("id",)])),
            "sale_status": str(extract_first(payload, [("event",), ("sale", "status"), ("status",)], "received")),
            "product_name": str(extract_first(payload, [("product", "name"), ("sale", "product_name")], "Produto Greenn")),
            "buyer_name": str(extract_first(payload, [("customer", "name"), ("buyer", "name")])),
            "buyer_email": str(extract_first(payload, [("customer", "email"), ("buyer", "email")])),
            "buyer_phone": digits_only(extract_first(payload, [("customer", "phone"), ("buyer", "phone")])),
            "amount_cents": as_cents(extract_first(payload, [("sale", "amount"), ("amount",)], 0)),
            "currency": str(extract_first(payload, [("sale", "currency"), ("currency",)], "BRL")),
        }

    return {
        "external_id": str(extract_first(payload, [("order_id",), ("id",), ("order", "id")])),
        "sale_status": str(extract_first(payload, [("order_status",), ("status",), ("event",)], "received")),
        "product_name": str(extract_first(payload, [("product_name",), ("product", "name")], "Produto Kiwify")),
        "buyer_name": str(extract_first(payload, [("Customer", "full_name"), ("customer", "name"), ("buyer", "name")])),
        "buyer_email": str(extract_first(payload, [("Customer", "email"), ("customer", "email"), ("buyer", "email")])),
        "buyer_phone": digits_only(extract_first(payload, [("Customer", "mobile"), ("customer", "phone"), ("buyer", "phone")])),
        "amount_cents": as_cents(extract_first(payload, [("order_ref", "Commissions", "charge_amount"), ("amount",), ("order", "amount")], 0)),
        "currency": str(extract_first(payload, [("currency",), ("order", "currency")], "BRL")),
    }


def store_event(platform, normalized, payload):
    with connect_sales_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sales_events (
                platform, external_id, sale_status, product_name,
                buyer_name, buyer_email, buyer_phone,
                amount_cents, currency, payload_json, received_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                platform,
                normalized["external_id"],
                normalized["sale_status"],
                normalized["product_name"],
                normalized["buyer_name"],
                normalized["buyer_email"],
                normalized["buyer_phone"],
                normalized["amount_cents"],
                normalized["currency"],
                json.dumps(payload, ensure_ascii=False),
                now_iso(),
            ),
        )


def maybe_notify_student(platform, normalized, config):
    student_phone = config.get("student_phone", "")
    if not student_phone:
        return False, "student_phone nao configurado"

    buyer = normalized["buyer_name"] or normalized["buyer_email"] or "cliente"
    amount = normalized["amount_cents"] / 100 if normalized["amount_cents"] else 0
    message = (
        f"💸 Nova venda capturada via {platform.title()}\n"
        f"Cliente: {buyer}\n"
        f"Produto: {normalized['product_name']}\n"
        f"Status: {normalized['sale_status']}\n"
        f"Valor: R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    if not should_send(student_phone, message, window_hours=1):
        return False, "notificacao duplicada"

    limiter = ZAPIRateLimiter()
    if not limiter.can_send(student_phone):
        return False, "rate limiter bloqueou"

    try:
        ok = send_whatsapp(student_phone, message, config)
    except Exception as exc:
        return False, f"falha no envio: {exc}"

    if ok:
        limiter.record_send(student_phone)
        log_dispatch(student_phone, message, f"week2-sale-{platform}")
        return True, "enviado"
    return False, "envio retornou false"


class WebhookHandler(BaseHTTPRequestHandler):
    server_version = "ZXControlWeek2/1.0"

    def _json_response(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._json_response(200, {"status": "ok", "service": "sales_webhooks"})
            return
        self._json_response(404, {"error": "not_found"})

    def do_POST(self):
        if not self.path.startswith("/webhook/"):
            self._json_response(404, {"error": "not_found"})
            return

        platform = self.path.removeprefix("/webhook/").strip().lower()
        if platform not in {"hotmart", "greenn", "kiwify"}:
            self._json_response(404, {"error": "platform_not_supported"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._json_response(400, {"error": "invalid_json"})
            return

        try:
            config = load_config()
            normalized = normalize_payload(platform, payload)
            store_event(platform, normalized, payload)
            notified, notify_detail = maybe_notify_student(platform, normalized, config)
        except Exception as exc:
            self._json_response(500, {"error": "processing_error", "detail": str(exc)})
            return

        self._json_response(
            200,
            {
                "status": "ok",
                "platform": platform,
                "external_id": normalized["external_id"],
                "notified": notified,
                "notify_detail": notify_detail,
            },
        )

    def log_message(self, format, *args):
        return


def main():
    parser = argparse.ArgumentParser(description="Servidor local de webhooks de venda")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8782)
    args = parser.parse_args()

    ensure_week2_structure()
    server = ThreadingHTTPServer((args.host, args.port), WebhookHandler)
    print(f"Webhooks ouvindo em http://{args.host}:{args.port}")
    print("Rotas: /webhook/hotmart, /webhook/greenn, /webhook/kiwify, /health")
    server.serve_forever()


if __name__ == "__main__":
    main()
