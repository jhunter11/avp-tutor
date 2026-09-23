"""Opt-in local feedback store; no background tracking or automatic training."""

import json
import os
import secrets
import sqlite3
import time
from pathlib import Path


class FeedbackStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id TEXT PRIMARY KEY, created REAL NOT NULL, request TEXT NOT NULL,
                    response TEXT NOT NULL, rating TEXT, comment TEXT DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY, created REAL NOT NULL, event TEXT NOT NULL,
                    algorithm TEXT NOT NULL
                );
            """)
            cutoff = time.time() - 30 * 86400
            db.execute("DELETE FROM interactions WHERE created < ?", (cutoff,))
            db.execute("DELETE FROM usage WHERE created < ?", (cutoff,))
        os.chmod(path, 0o600)

    def connect(self):
        return sqlite3.connect(self.path, timeout=5)

    def record(self, request, response):
        id = secrets.token_urlsafe(32)
        with self.connect() as db:
            db.execute(
                "INSERT INTO interactions (id,created,request,response) VALUES (?,?,?,?)",
                (id, time.time(), json.dumps(request), json.dumps(response)),
            )
        return id

    def add_feedback(self, id, rating, comment):
        with self.connect() as db:
            cursor = db.execute(
                "UPDATE interactions SET rating=?,comment=? WHERE id=?",
                (rating, comment, id),
            )
            if cursor.rowcount != 1:
                raise KeyError(id)

    def delete(self, id):
        with self.connect() as db:
            return db.execute("DELETE FROM interactions WHERE id=?", (id,)).rowcount > 0

    def review_rows(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT id,request,response,rating,comment FROM interactions WHERE rating IS NOT NULL ORDER BY created"
            ).fetchall()
        return [
            {
                "id": id,
                "request": json.loads(request),
                "response": json.loads(response),
                "rating": rating,
                "comment": comment,
            }
            for id, request, response, rating, comment in rows
        ]

    def record_usage(self, event, algorithm):
        with self.connect() as db:
            db.execute(
                "INSERT INTO usage (created,event,algorithm) VALUES (?,?,?)",
                (time.time(), event, algorithm),
            )

    def usage_summary(self):
        with self.connect() as db:
            return dict(
                db.execute("SELECT event,count(*) FROM usage GROUP BY event").fetchall()
            )


def feedback_enabled():
    return os.environ.get("FEEDBACK_ENABLED", "false").lower() == "true"


def get_store():
    if not feedback_enabled():
        raise RuntimeError("Feedback capture is disabled")
    return FeedbackStore(
        Path(
            os.environ.get(
                "FEEDBACK_DB_PATH",
                str(
                    Path(__file__).resolve().parent.parent
                    / "artifacts"
                    / "feedback.sqlite3"
                ),
            )
        )
    )
