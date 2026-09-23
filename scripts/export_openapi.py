"""Export the frontend integration contract without starting a model/server."""

import json
from pathlib import Path

from api.main import app


def main():
    output = Path(__file__).resolve().parent.parent / "integrations" / "openapi.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n")
    print(output)


if __name__ == "__main__":
    main()
