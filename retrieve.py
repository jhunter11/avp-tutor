"""Lightweight lexical retrieval by default; optional upstream BGE/FAISS backend."""

import json
import os
from pathlib import Path
from threading import Lock

from tutor.knowledge import tokens

ROOT = Path(__file__).resolve().parent
_retriever = None
_lock = Lock()


class LexicalCodeRetriever:
    def __init__(self, knowledge_base_path=None):
        path = (
            Path(knowledge_base_path)
            if knowledge_base_path
            else ROOT / "code_knowledge_base.json"
        )
        if path.exists():
            data = json.loads(path.read_text())
            self.chunks = data if isinstance(data, list) else data["chunks"]
        else:
            from ingest import parse_file

            self.chunks = []
            for source in sorted((ROOT / "data").glob("*.avp")):
                try:
                    self.chunks.extend(
                        parse_file(
                            str(source), source_file=str(source.relative_to(ROOT))
                        )
                    )
                except ValueError:
                    # Old corpus examples may not conform to the current grammar.
                    continue

    def retrieve(self, query, k=5):
        terms = set(tokens(query))
        matches = []
        for item in self.chunks:
            words = set(tokens(item["name"] + " " + item["code_content"]))
            score = len(terms & words) / max(len(terms), 1)
            if score:
                matches.append(
                    {
                        "score": score,
                        "function_name": item["name"],
                        "parameters": item.get("parameters", []),
                        "code": item["code_content"],
                        "source_file": item.get("source_file", ""),
                    }
                )
        return sorted(matches, key=lambda m: (-m["score"], m["function_name"]))[:k]


def get_retriever():
    global _retriever
    with _lock:
        if _retriever is None:
            if os.environ.get("RETRIEVAL_BACKEND", "lexical") == "semantic":
                try:
                    from semantic_retrieve import CodeRetriever
                except (ImportError, SystemExit) as exc:
                    raise RuntimeError(
                        "Install the semantic extra and run ingest.py before selecting semantic retrieval."
                    ) from exc
                _retriever = CodeRetriever(
                    device=os.environ.get("EMBEDDING_DEVICE", "cpu")
                )
            else:
                _retriever = LexicalCodeRetriever()
    return _retriever


def retrieve_code(query: str, k: int = 2):
    return get_retriever().retrieve(query, k=k)
