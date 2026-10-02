"""Bounded repository examples; never substitute their state for the current run."""

import hashlib
import re
from pathlib import Path

from tutor.models import CodeExample, TutorRequest
from tutor.validation import validate_avp

DATA = Path(__file__).resolve().parent.parent / "data"


def normalize_algorithm(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def select_examples(request: TutorRequest, k: int = 1) -> list[CodeExample]:
    if not request.context or not request.context.algorithm or k <= 0:
        return []
    examples = []
    remaining = 6000
    algorithm = normalize_algorithm(request.context.algorithm)
    for path in sorted(DATA.glob("*.avp")):
        if normalize_algorithm(path.stem) != algorithm:
            continue
        if path.stat().st_size > 24000:
            continue
        code = path.read_text()
        if len(code) > remaining or code.strip() == request.context.code.strip():
            continue
        if not validate_avp(code).syntax_valid:
            continue
        examples.append(
            CodeExample(
                id=f"example:{path.stem}",
                algorithm=path.stem,
                path=f"data/{path.name}",
                code=code,
                code_sha256=hashlib.sha256(code.encode()).hexdigest(),
            )
        )
        remaining -= len(code)
        if len(examples) >= min(k, 2):
            break
    return examples
