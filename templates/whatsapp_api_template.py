#!/usr/bin/env python3
"""
Abstracao simples para envio de WhatsApp via Evolution API ou Z-API.
"""

import json
import urllib.request


def _post_json(url, payload, headers=None):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        data = json.loads(body) if body else {}
        return response.status, data


def send_whatsapp(phone, text, config):
    provider = config.get("whatsapp_provider")

    if provider == "evolution":
        evolution = config.get("evolution", {})
        base_url = evolution.get("base_url", "http://localhost:8080").rstrip("/")
        api_key = evolution.get("api_key")
        instance_name = evolution.get("instance_name", "operacao-ia")
        status, _ = _post_json(
            f"{base_url}/message/sendText/{instance_name}",
            {"number": phone, "text": text},
            headers={"apikey": api_key},
        )
        return status in (200, 201)

    if provider == "zapi":
        zapi = config.get("zapi", {})
        instance_id = zapi.get("instance_id")
        token = zapi.get("token")
        status, _ = _post_json(
            f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text",
            {"phone": phone, "message": text},
        )
        return status in (200, 201)

    raise ValueError(f"Provedor WhatsApp nao suportado: {provider}")
