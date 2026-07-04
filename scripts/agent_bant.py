#!/usr/bin/env python3
"""
Agente IA BANT da Operacao IA.
Este arquivo e a fonte do script deployado em ~/.operacao-ia/scripts/agent_bant.py.
"""

import hashlib
import json
import logging
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = SCRIPT_DIR.parent / "templates"
sys.path.insert(0, str(SCRIPT_DIR))
if TEMPLATES_DIR.exists():
    sys.path.insert(0, str(TEMPLATES_DIR))

from dispatch_log_template import log_dispatch, should_send
from rate_limiter_template import ZAPIRateLimiter
from whatsapp_api_template import send_whatsapp


CONFIG_PATH = Path.home() / ".operacao-ia" / "config" / "config.json"
SESSIONS_DB = Path.home() / ".operacao-ia" / "data" / "sessions.db"
AGENT_STATE = Path.home() / ".operacao-ia" / "data" / ".agent_state.json"
DEFAULT_AGENT_PORT = 8781
SESSION_TTL = 1800
STATE_CACHE_LIMIT = 5000

DEFAULT_AGENT_NAME = "{{AGENT_NAME}}"
DEFAULT_AGENT_TONE = "{{AGENT_TONE}}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("agent-bant")


def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError("config.json nao encontrado em ~/.operacao-ia/config/")
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def db():
    SESSIONS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(SESSIONS_DB))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            phone TEXT PRIMARY KEY,
            messages TEXT NOT NULL,
            last_activity REAL NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def load_session(phone):
    with db() as conn:
        row = conn.execute(
            "SELECT messages, last_activity FROM sessions WHERE phone = ?",
            (phone,),
        ).fetchone()
    if not row:
        return None
    return {"messages": json.loads(row[0]), "last_activity": float(row[1])}


def save_session(phone, messages, last_activity):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (phone, messages, last_activity) VALUES (?, ?, ?)",
            (phone, json.dumps(messages, ensure_ascii=False), last_activity),
        )
        conn.commit()


def cleanup_expired_sessions():
    cutoff = time.time() - SESSION_TTL
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE last_activity < ?", (cutoff,))
        conn.commit()


def build_system_prompt(config):
    agent_name = config.get("agent_name") or DEFAULT_AGENT_NAME or "Ana"
    agent_tone = config.get("agent_tone") or DEFAULT_AGENT_TONE or "vendas"
    business_name = config.get("business_name", "Operacao IA")

    tone_map = {
        "vendas": "consultiva, persuasiva, leve e objetiva",
        "suporte": "prestativa, clara, acolhedora e calma",
        "geral": "natural, humana, objetiva e amigavel",
    }
    tone_text = tone_map.get(agent_tone, tone_map["geral"])

    return f"""
Voce e {agent_name}, atendente da {business_name}.

Objetivo:
- Conduzir conversas de WhatsApp com naturalidade.
- Qualificar a pessoa usando BANT de forma sutil.
- Levar a conversa para fechamento ou proximo passo quando fizer sentido.

Metodo BANT:
- Budget: entender capacidade ou abertura para investir
- Authority: descobrir se a pessoa decide ou consulta alguem
- Need: identificar a dor real e o objetivo
- Timeline: entender urgencia e quando quer agir

Regras:
- Responda em portugues do Brasil.
- Nunca soe robotica.
- Use no maximo 3 a 5 linhas por resposta.
- Faca uma pergunta por vez.
- Evite listas longas.
- Seja pratica e humana.
- Se faltar contexto, pergunte antes de assumir.
- Se a pessoa demonstrar forte interesse, convide para o proximo passo de forma natural.
- Nao invente promessas, numeros ou garantias que nao estejam na conversa.

Tom:
- {tone_text}
"""


def call_openai(messages, api_key, system_prompt):
    payload = json.dumps(
        {
            "model": "gpt-4o-mini",
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_completion_tokens": 600,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"].strip()


def call_gemini(messages, api_key, system_prompt):
    contents = []
    for message in [{"role": "system", "content": system_prompt}] + messages:
        role = "model" if message["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": message["content"]}]})

    payload = json.dumps(
        {
            "contents": contents,
            "generationConfig": {"maxOutputTokens": 1500, "temperature": 0.7},
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def call_anthropic(messages, api_key, system_prompt):
    payload = json.dumps(
        {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 700,
            "system": system_prompt,
            "messages": messages,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        result = json.loads(response.read().decode("utf-8"))
    return "".join(item.get("text", "") for item in result.get("content", [])).strip()


def generate_reply(config, messages):
    provider = (config.get("ai_provider") or "").lower()
    api_key = config.get("ai_api_key", "")
    prompt = build_system_prompt(config)

    if provider == "openai":
        return call_openai(messages, api_key, prompt)
    if provider == "gemini":
        return call_gemini(messages, api_key, prompt)
    if provider == "anthropic":
        return call_anthropic(messages, api_key, prompt)

    raise ValueError(f"Provider de IA nao suportado: {provider}")


def normalize_phone(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if digits.startswith("55") and len(digits) >= 12:
        return digits
    return digits


def is_inbound_evolution(payload):
    event = payload.get("event")
    if event and event != "messages.upsert":
        return False
    data = payload.get("data", {})
    if isinstance(data, dict) and data.get("key", {}).get("fromMe"):
        return False
    return True


def extract_evolution_message(payload):
    data = payload.get("data", {}) if isinstance(payload, dict) else {}
    key = data.get("key", {}) if isinstance(data, dict) else {}
    message = data.get("message", {}) if isinstance(data, dict) else {}

    remote_jid = key.get("remoteJid", "")
    if remote_jid.endswith("@g.us"):
        return None, None

    text = (
        message.get("conversation")
        or message.get("extendedTextMessage", {}).get("text")
        or message.get("imageMessage", {}).get("caption")
        or ""
    ).strip()
    phone = normalize_phone(remote_jid.replace("@s.whatsapp.net", ""))
    return phone, text


def load_agent_state():
    if not AGENT_STATE.exists():
        return {"seen_message_ids": []}
    try:
        state = json.loads(AGENT_STATE.read_text(encoding="utf-8"))
        state.setdefault("seen_message_ids", [])
        return state
    except Exception:
        return {"seen_message_ids": []}


def save_agent_state(state):
    state["seen_message_ids"] = state.get("seen_message_ids", [])[-STATE_CACHE_LIMIT:]
    AGENT_STATE.parent.mkdir(parents=True, exist_ok=True)
    AGENT_STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def build_message_id(phone, text, raw_id=""):
    if raw_id:
        return str(raw_id)
    return hashlib.sha256(f"{phone}|{text}".encode("utf-8")).hexdigest()


def was_seen(state, message_id):
    return message_id in state.get("seen_message_ids", [])


def mark_seen(state, message_id):
    state.setdefault("seen_message_ids", []).append(message_id)
    if len(state["seen_message_ids"]) > STATE_CACHE_LIMIT:
        state["seen_message_ids"] = state["seen_message_ids"][-STATE_CACHE_LIMIT:]


_zapi_inbound_warned = False


def extract_zapi_messages(config):
    global _zapi_inbound_warned
    zapi = config.get("zapi", {})
    messages_file = zapi.get("messages_file")
    if not messages_file:
        if not _zapi_inbound_warned:
            log.warning(
                "Z-API inbound nao configurado — a Z-API entrega mensagens por webhook, "
                "nao por arquivo local. Configure 'zapi.messages_file' no config.json com o "
                "arquivo onde seu webhook Z-API grava as mensagens recebidas."
            )
            _zapi_inbound_warned = True
        return []
    messages_file = Path(messages_file)
    if not messages_file.exists():
        return []
    try:
        data = json.loads(messages_file.read_text(encoding="utf-8"))
    except Exception:
        return []
    return data if isinstance(data, list) else []


def extract_zapi_text(entry):
    text = entry.get("text", "")
    if isinstance(text, dict):
        text = text.get("message", "")
    if not isinstance(text, str):
        text = ""
    return text.strip()


def evolution_request(config, endpoint, payload):
    evolution = config.get("evolution", {})
    base_url = evolution.get("base_url", "http://localhost:8080").rstrip("/")
    api_key = evolution.get("api_key", "")
    instance = evolution.get("instance_name", "operacao-ia")
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{endpoint}/{instance}",
        data=data,
        headers={"Content-Type": "application/json", "apikey": api_key},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = response.read()
        result = json.loads(body.decode("utf-8")) if body else {}
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        if "messages" in result and isinstance(result["messages"], dict):
            return result["messages"].get("records", [])
        if "messages" in result and isinstance(result["messages"], list):
            return result["messages"]
        if "chats" in result:
            return result["chats"]
        if "records" in result:
            return result["records"]
    return result if isinstance(result, list) else []


def fetch_evolution_chats(config):
    return evolution_request(config, "/chat/findChats", {})


def fetch_evolution_messages(config, jid, limit=15):
    return evolution_request(
        config,
        "/chat/findMessages",
        {"where": {"key": {"remoteJid": jid}}, "limit": limit},
    )


def extract_text_from_evolution_record(record):
    msg_data = record.get("message") or {}
    return (
        msg_data.get("conversation")
        or (msg_data.get("extendedTextMessage") or {}).get("text", "")
        or (msg_data.get("imageMessage") or {}).get("caption", "")
        or ""
    ).strip()


def send_agent_reply(phone, reply, config):
    limiter = ZAPIRateLimiter()
    if not should_send(phone, reply, window_hours=1):
        log.info("resposta duplicada pulada para %s", phone)
        return False
    if not limiter.can_send(phone):
        log.warning("rate limiter bloqueou resposta para %s", phone)
        return False
    if send_whatsapp(phone, reply, config):
        limiter.record_send(phone)
        log_dispatch(phone, reply, "agent-bant-reply")
        log.info("resposta enviada para %s", phone)
        return True
    log.error("falha ao enviar resposta para %s", phone)
    return False


def process_message(phone, text, config):
    cleanup_expired_sessions()
    if not phone or not text:
        return

    session = load_session(phone) or {"messages": [], "last_activity": time.time()}
    session["messages"].append({"role": "user", "content": text})
    session["last_activity"] = time.time()

    try:
        reply = generate_reply(config, session["messages"])
    except Exception as exc:
        log.error("erro IA: %s", exc)
        reply = "Tive uma instabilidade agora. Me responde de novo em alguns segundos?"

    session["messages"].append({"role": "assistant", "content": reply})
    save_session(phone, session["messages"], session["last_activity"])
    send_agent_reply(phone, reply, config)


class EvolutionWebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)

        try:
            payload = json.loads(body.decode("utf-8"))
            if is_inbound_evolution(payload):
                phone, text = extract_evolution_message(payload)
                process_message(phone, text, self.server.config)
        except Exception as exc:
            log.error("erro webhook evolution: %s", exc)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok"}')

    def log_message(self, format, *args):
        return


def run_evolution_server(config):
    port = int(config.get("agent_port") or DEFAULT_AGENT_PORT)
    server = HTTPServer(("127.0.0.1", port), EvolutionWebhookHandler)
    server.config = config
    log.info("agent BANT ouvindo webhooks Evolution em http://127.0.0.1:%s/webhook", port)
    server.serve_forever()


def run_evolution_polling(config):
    log.info("agent BANT em polling Evolution")
    state = load_agent_state()
    while True:
        try:
            chats = fetch_evolution_chats(config)
            for chat in chats:
                jid = chat.get("id") or chat.get("remoteJid") or ""
                if not jid or jid.endswith("@g.us"):
                    continue
                records = fetch_evolution_messages(config, jid, limit=10)
                for record in records:
                    key = record.get("key") or {}
                    if key.get("fromMe"):
                        continue
                    phone = normalize_phone((key.get("remoteJid") or jid).replace("@s.whatsapp.net", ""))
                    text = extract_text_from_evolution_record(record)
                    message_id = build_message_id(phone, text, key.get("id", ""))
                    if not text or was_seen(state, message_id):
                        continue
                    process_message(phone, text, config)
                    mark_seen(state, message_id)
            save_agent_state(state)
        except Exception as exc:
            log.error("erro polling evolution: %s", exc)
        time.sleep(3)


def run_zapi_polling(config):
    log.info("agent BANT em polling Z-API")
    state = load_agent_state()
    while True:
        try:
            messages = extract_zapi_messages(config)
            for entry in messages:
                if entry.get("fromMe") or entry.get("isGroup"):
                    continue
                phone = normalize_phone(entry.get("phone", ""))
                text = extract_zapi_text(entry)
                raw_id = entry.get("messageId") or entry.get("id") or entry.get("message_id") or ""
                message_id = build_message_id(phone, text, raw_id)
                if not text or was_seen(state, message_id):
                    continue
                process_message(phone, text, config)
                mark_seen(state, message_id)
            save_agent_state(state)
        except Exception as exc:
            log.error("erro polling zapi: %s", exc)
        time.sleep(3)


def main():
    config = load_config()
    provider = config.get("whatsapp_provider")
    if provider == "evolution":
        run_evolution_polling(config)
    elif provider == "zapi":
        run_zapi_polling(config)
    else:
        raise SystemExit(f"whatsapp_provider invalido: {provider}")


if __name__ == "__main__":
    main()
