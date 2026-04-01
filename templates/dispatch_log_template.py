#!/usr/bin/env python3
"""
Template de log de disparos com deduplicacao por conteudo.
"""

import hashlib
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path.home() / ".operacao-ia" / "data" / "dispatch_log.db"


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dispatch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            dispatch_type TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_dispatch_lookup
        ON dispatch_log(recipient, content_hash, sent_at)
        """
    )
    return conn


def _hash_content(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def should_send(recipient, content, window_hours=24):
    content_hash = _hash_content(content)
    cutoff = (datetime.now() - timedelta(hours=window_hours)).isoformat()

    with _connect() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM dispatch_log
            WHERE recipient = ? AND content_hash = ? AND sent_at >= ?
            """,
            (recipient, content_hash, cutoff),
        ).fetchone()

    return int(row[0]) == 0 if row else True


def log_dispatch(recipient, content, dtype):
    content_hash = _hash_content(content)
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO dispatch_log (recipient, content_hash, sent_at, dispatch_type)
            VALUES (?, ?, ?, ?)
            """,
            (recipient, content_hash, datetime.now().isoformat(), dtype),
        )
