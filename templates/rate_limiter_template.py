#!/usr/bin/env python3
"""
Template de rate limiter local para disparos WhatsApp.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


DB_PATH = Path.home() / ".operacao-ia" / "data" / "rate_limiter.db"


class ZAPIRateLimiter:
    def __init__(self, db_path=None, max_per_hour=30, max_per_day=150, min_interval_seconds=90):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.min_interval_seconds = min_interval_seconds
        self._ensure_db()

    def _connect(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(str(self.db_path))

    def _ensure_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT NOT NULL,
                    sent_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sends_sent_at ON sends(sent_at)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_sends_recipient ON sends(recipient)"
            )

    def _count_since(self, since):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM sends WHERE sent_at >= ?",
                (since.isoformat(),),
            ).fetchone()
        return int(row[0]) if row else 0

    def _last_send_at(self, phone):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT sent_at
                FROM sends
                WHERE recipient = ?
                ORDER BY sent_at DESC
                LIMIT 1
                """,
                (phone,),
            ).fetchone()

        if not row:
            return None
        return datetime.fromisoformat(row[0])

    def can_send(self, phone):
        now = datetime.now()
        if self._count_since(now - timedelta(hours=1)) >= self.max_per_hour:
            return False
        if self._count_since(now - timedelta(days=1)) >= self.max_per_day:
            return False

        last_send = self._last_send_at(phone)
        if last_send and (now - last_send).total_seconds() < self.min_interval_seconds:
            return False

        return True

    def record_send(self, phone):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO sends (recipient, sent_at) VALUES (?, ?)",
                (phone, datetime.now().isoformat()),
            )

    @contextmanager
    def sending(self, phone):
        if not self.can_send(phone):
            raise RuntimeError(f"Rate limit ativo para {phone}")

        try:
            yield self
        except Exception:
            raise
        else:
            self.record_send(phone)
