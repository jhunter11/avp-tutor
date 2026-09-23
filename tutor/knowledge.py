"""Small, deterministic BM25-style teaching-note retrieval with source provenance."""

import hashlib
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

from tutor.models import Source

ROOT = Path(__file__).resolve().parent.parent
STOP = set(
    "a an the is it this that of to in on and or for why how what does do we i me please explain".split()
)


def tokens(text):
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


@lru_cache(maxsize=1)
def load_notes():
    notes = []
    for path in sorted((ROOT / "knowledge").glob("*.md")):
        title = path.read_text().splitlines()[0].lstrip("# ")
        for section in re.split(r"(?m)^## ", path.read_text())[1:]:
            heading, _, body = section.partition("\n")
            slug = re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
            notes.append(
                Source(
                    id=f"{path.stem}:{slug}",
                    title=title,
                    section=heading,
                    path=f"knowledge/{path.name}",
                    text=body.strip(),
                )
            )
    return notes


def knowledge_version():
    return hashlib.sha256(
        "".join(s.model_dump_json() for s in load_notes()).encode()
    ).hexdigest()[:12]


def retrieve_notes(query: str, algorithm: str = "", k: int = 3) -> list[Source]:
    notes = load_notes()
    query_terms = set(tokens(query))
    algo_terms = set(tokens(algorithm))
    docs = [Counter(tokens(f"{s.title} {s.section} {s.text}")) for s in notes]
    avg_len = sum(sum(d.values()) for d in docs) / max(len(docs), 1)
    ranked = []
    for source, counts in zip(notes, docs):
        score = 0.0
        # With an explicit algorithm, unrelated algorithm chapters are excluded.
        title_terms = set(tokens(source.title))
        if (
            algo_terms
            and not algo_terms <= title_terms
            and source.path != "knowledge/avp.md"
        ):
            continue
        for term in query_terms | algo_terms:
            tf = counts[term]
            if not tf:
                continue
            df = sum(term in d for d in docs)
            idf = math.log(1 + (len(docs) - df + 0.5) / (df + 0.5))
            score += (
                idf
                * tf
                * 2.2
                / (tf + 1.2 * (0.25 + 0.75 * sum(counts.values()) / max(avg_len, 1)))
            )
        if score > 0:
            ranked.append((score, source))
    ranked.sort(key=lambda item: (-item[0], item[1].id))
    return [source for _, source in ranked[:k]]
