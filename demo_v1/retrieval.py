"""Small local TF-IDF vectors, kept separate from algorithm facts."""

import json
import math
import re
from collections import Counter
from pathlib import Path

from tutor.models import Source

ROOT = Path(__file__).resolve().parent


def terms(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def rank(query, records, k=2):
    if not records:
        return []
    docs = [Counter(terms(r["text"] + " " + r.get("title", ""))) for r in records]
    query_counts = Counter(terms(query))
    vocabulary = set().union(*docs)
    idf = {
        term: math.log((1 + len(docs)) / (1 + sum(term in d for d in docs))) + 1
        for term in vocabulary
    }

    def vector(counts):
        raw = {t: count * idf[t] for t, count in counts.items() if t in idf}
        norm = math.sqrt(sum(v * v for v in raw.values())) or 1
        return {t: value / norm for t, value in raw.items()}

    q = vector(query_counts)
    scores = [
        (sum(value * q.get(t, 0) for t, value in vector(d).items()), record)
        for d, record in zip(docs, records)
    ]
    return [
        r
        for score, r in sorted(scores, key=lambda item: (-item[0], item[1]["id"]))[:k]
        if score > 0
    ]


def retrieve_methods(query):
    records = json.loads((ROOT / "pedagogy.json").read_text(encoding="utf-8"))
    return rank(query, records)


def method_sources(records):
    return [
        Source(**{k: r[k] for k in ("id", "title", "path", "section", "text")})
        for r in records
    ]
