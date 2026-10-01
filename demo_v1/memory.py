"""Explicit learner notes in a separate local store. No automatic self-training."""

import os
import re
import secrets
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from demo_v1.retrieval import rank

SECRET = re.compile(
    r"AIza[\w-]{25,}|\bsk-[\w-]{16,}|(?:api[_ -]?key|password|secret|token)\s*[:=]\s*\S+|Bearer\s+\S+",
    re.I,
)


def reject_secret(text):
    if SECRET.search(text):
        raise ValueError(
            "Remove credentials before saving a note or sending a question."
        )
    return text


def default_path():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData/Local")))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local/share")))
    return Path(
        os.environ.get(
            "AVP_DEMO_MEMORY_PATH", str(base / "avp-tutor-v1" / "learner.sqlite3")
        )
    )


class LearnerMemory:
    def __init__(self, path=None):
        self.path = path or default_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS notes (id TEXT PRIMARY KEY, created TEXT NOT NULL, text TEXT NOT NULL)"
            )

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def notes(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,created,text FROM notes ORDER BY created DESC LIMIT 50"
            ).fetchall()
        return [
            {
                "id": row[0],
                "created": row[1],
                "text": row[2],
                "title": "User-reviewed learning note",
                "status": "User report, not verified mastery",
            }
            for row in rows
        ]

    def add(self, text):
        text = reject_secret(text.strip())
        if not 1 <= len(text) <= 400:
            raise ValueError("Write a learning note of 1 to 400 characters.")
        with self.connect() as db:
            if db.execute("SELECT count(*) FROM notes").fetchone()[0] >= 50:
                raise ValueError("The note limit is 50. Delete an old note first.")
            db.execute(
                "INSERT INTO notes VALUES (?,?,?)",
                (secrets.token_hex(12), datetime.now(UTC).isoformat(), text),
            )

    def delete(self, note_id):
        with self.connect() as db:
            return db.execute("DELETE FROM notes WHERE id=?", (note_id,)).rowcount == 1

    def recall(self, query):
        return rank(query, self.notes(), k=2)
