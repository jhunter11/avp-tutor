"""Inventory source teaching material and parse every original AVP example."""

import json
from pathlib import Path

from tutor.validation import validate_avp


def main():
    root = Path(__file__).resolve().parent.parent
    rows = []
    for path in sorted((root / "data").glob("*.avp")):
        result = validate_avp(path.read_text())
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "lines": len(path.read_text().splitlines()),
                **result.model_dump(),
            }
        )
    print(
        json.dumps(
            {
                "source_documents": ["Pseudocode.g4", "PseudocodeSyntax.md"],
                "files": rows,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
