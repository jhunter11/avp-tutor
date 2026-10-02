"""Fetch pinned public teaching resources, outside live RAG and approved training."""

import argparse
import hashlib
import json
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def install_file(root, entry, data):
    destination = (root / entry["path"]).resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError("Unsafe dataset path")
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise ValueError("Dataset checksum mismatch: " + entry["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    temporary.write_bytes(data)
    temporary.replace(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", help="Fetch only one source ID")
    parser.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/public-datasets"
    )
    args = parser.parse_args()
    lock = json.loads((ROOT / "datasets/sources.lock.json").read_text())
    selected = [x for x in lock["sources"] if not args.source or x["id"] == args.source]
    if not selected:
        parser.error("Unknown source ID")
    report = []
    with httpx.Client(timeout=60, follow_redirects=True) as client:
        for source in selected:
            count = 0
            for entry in source["files"]:
                path = args.output / entry["path"]
                if (
                    path.is_file()
                    and hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
                ):
                    count += 1
                    continue
                response = client.get(entry["url"])
                response.raise_for_status()
                install_file(args.output, entry, response.content)
                count += 1
            report.append(
                {"id": source["id"], "verified_files": count, "scope": source["scope"]}
            )
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "receipt.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
