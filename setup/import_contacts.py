#!/usr/bin/env python3
"""
Importa contatos para ~/.operacao-ia/data/contacts.db e gera backup CSV.
"""

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path.home() / ".operacao-ia"
DATA_DIR = BASE_DIR / "data"
CONFIG_PATH = BASE_DIR / "config" / "config.json"
CONTACTS_DB = DATA_DIR / "contacts.db"
CONTACTS_CSV = DATA_DIR / "contacts.csv"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def ensure_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CONTACTS_DB))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            imported_at TEXT NOT NULL,
            tags TEXT DEFAULT ''
        )
        """
    )
    conn.commit()
    return conn


def normalize_phone(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return ""
    if not digits.startswith("55"):
        digits = "55" + digits
    if len(digits) < 12:
        return ""
    return digits


def parse_inline_contacts(first_line):
    print("Cole um contato por linha no formato nome,telefone ou nome,telefone,tag.")
    print("Finalize com uma linha vazia.")
    lines = [first_line]
    while True:
        line = input().strip()
        if not line:
            break
        lines.append(line)

    entries = []
    for raw in lines:
        if "," not in raw:
            continue
        parts = [item.strip() for item in raw.split(",")]
        name = parts[0] if len(parts) >= 1 else ""
        phone = parts[1] if len(parts) >= 2 else ""
        tags = ",".join(parts[2:]) if len(parts) >= 3 else ""
        entries.append({"name": name, "phone": phone, "source": "manual", "tags": tags})
    return entries


def detect_delimiter(sample):
    candidates = [",", ";", "\t"]
    counts = {sep: sample.count(sep) for sep in candidates}
    return max(counts, key=counts.get)


def resolve_column(fieldnames, options):
    names = [f.strip().lower() for f in (fieldnames or [])]
    for option in options:
        if option in names:
            return fieldnames[names.index(option)]
    return None


def parse_csv_contacts(path):
    content = Path(path).read_text(encoding="utf-8")
    delimiter = detect_delimiter(content[:1000])
    reader = csv.DictReader(content.splitlines(), delimiter=delimiter)
    name_col = resolve_column(reader.fieldnames, ["name", "nome"])
    phone_col = resolve_column(reader.fieldnames, ["phone", "telefone", "numero"])
    tags_col = resolve_column(reader.fieldnames, ["tags", "tag", "etiqueta", "etiquetas"])
    if not name_col or not phone_col:
        raise SystemExit("CSV invalido: colunas esperadas name/nome e phone/telefone/numero")

    entries = []
    for row in reader:
        entries.append(
            {
                "name": (row.get(name_col) or "").strip(),
                "phone": (row.get(phone_col) or "").strip(),
                "source": str(path),
                "tags": (row.get(tags_col) or "").strip() if tags_col else "",
            }
        )
    return entries


def backup_contacts(rows):
    with CONTACTS_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["name", "phone", "source", "imported_at", "tags"])
        writer.writeheader()
        writer.writerows(rows)


def export_current_contacts():
    with ensure_db() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT name, phone, source, imported_at, tags FROM contacts ORDER BY name, phone"
        ).fetchall()
    return [dict(row) for row in rows]


def main():
    print()
    print("Importacao de contatos")
    print("=" * 50)
    print()

    _ = load_config()
    raw = input("Cole seus contatos (nome,telefone) ou informe o caminho de um CSV: ").strip()
    if not raw:
        raise SystemExit("Nenhum dado informado.")

    source_path = Path(raw).expanduser()
    if source_path.exists():
        contacts = parse_csv_contacts(source_path)
    else:
        contacts = parse_inline_contacts(raw)

    imported = 0
    invalid = 0
    imported_at = datetime.now().isoformat()

    with ensure_db() as conn:
        for entry in contacts:
            name = entry["name"].strip()
            phone = normalize_phone(entry["phone"])
            if not name or not phone:
                invalid += 1
                continue
            try:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO contacts (name, phone, source, imported_at, tags)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, phone, entry["source"], imported_at, entry.get("tags", "")),
                )
                imported += 1
            except Exception:
                invalid += 1
        conn.commit()

    backup_contacts(export_current_contacts())

    print()
    print(f"✅ {imported} contatos importados, {invalid} invalidos ignorados")
    print(f"  Banco:  {CONTACTS_DB}")
    print(f"  Backup: {CONTACTS_CSV}")
    print()


if __name__ == "__main__":
    main()
