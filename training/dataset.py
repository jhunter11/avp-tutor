"""Validate tutoring interactions and export leakage-resistant chat datasets."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from harness.config import harness_version, load_config
from tutor.knowledge import knowledge_version
from tutor.models import StrictModel, TutorRequest
from tutor.service import PROMPT_VERSION, build_messages, sources_for_request


class Example(StrictModel):
    id: str = Field(min_length=1)
    algorithm: str = Field(min_length=1)
    program_id: str = Field(min_length=1)
    trace_id: str = Field(min_length=1)
    provenance: Literal["synthetic-draft", "human-authored", "consented-session"]
    review_status: Literal["draft", "approved"] = "draft"
    reviewed_by: str = ""
    request: TutorRequest
    answer: str = Field(min_length=1, max_length=8000)
    expected_facts: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def approval(self) -> Self:
        if self.review_status == "approved" and not self.reviewed_by.strip():
            raise ValueError("approved examples require reviewed_by")
        if self.request.context and self.request.context.algorithm != self.algorithm:
            raise ValueError("algorithm must match execution context")
        return self


def validate_examples(rows: list[dict]) -> list[Example]:
    examples = [Example.model_validate(row) for row in rows]
    seen = set()
    content = set()
    for row in examples:
        if row.id in seen:
            raise ValueError(f"Duplicate example ID: {row.id}")
        seen.add(row.id)
        digest = hashlib.sha256(
            (row.request.model_dump_json() + row.answer).encode()
        ).hexdigest()
        if digest in content:
            raise ValueError(f"Duplicate interaction: {row.id}")
        content.add(digest)
    return examples


def read_examples(path: Path) -> list[Example]:
    return validate_examples(
        [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    )


def group_examples(examples):
    # Connected components prevent aliases from splitting the same algorithm,
    # program, trace, or identical nonempty source code across partitions.
    groups = []
    for example in examples:
        keys = {
            "algorithm:" + example.algorithm,
            "program:" + example.program_id,
            "trace:" + example.trace_id,
        }
        if example.request.context and example.request.context.code.strip():
            normalized = "\n".join(
                line.strip()
                for line in example.request.context.code.splitlines()
                if line.strip()
            )
            keys.add("code:" + hashlib.sha256(normalized.encode()).hexdigest())
        matched = [g for g in groups if keys & g[0]]
        members = [example]
        for group in matched:
            keys.update(group[0])
            members.extend(group[1])
            groups.remove(group)
        groups.append((keys, members))
    return sorted(
        groups,
        key=lambda g: hashlib.sha256("\n".join(sorted(g[0])).encode()).hexdigest(),
    )


def export_dataset(examples: list[Example], output: Path, include_drafts=False):
    config = load_config()
    selected = [e for e in examples if include_drafts or e.review_status == "approved"]
    groups = group_examples(selected)
    partitions = {"train": [], "validation": [], "test": []}
    n_test = max(1, len(groups) // 10) if len(groups) >= 3 else 0
    n_val = max(1, len(groups) // 10) if len(groups) >= 3 else 0
    n_train = len(groups) - n_test - n_val
    for index, (_, members) in enumerate(groups):
        partition = (
            "train"
            if index < n_train
            else "validation"
            if index < n_train + n_val
            else "test"
        )
        partitions[partition].extend(sorted(members, key=lambda e: e.id))
    output.mkdir(parents=True, exist_ok=True)
    for partition, members in partitions.items():
        records = []
        for example in members:
            sources = sources_for_request(example.request, config)
            messages = build_messages(example.request, sources, config)
            messages.append({"role": "assistant", "content": example.answer})
            records.append(json.dumps({"messages": messages}, ensure_ascii=False))
        (output / f"{partition}.jsonl").write_text(
            "\n".join(records) + ("\n" if records else "")
        )
    manifest = {
        "exported": len(selected),
        "excluded_unreviewed": len(examples) - len(selected),
        "contains_drafts": any(e.review_status == "draft" for e in selected),
        "groups": len(groups),
        "split_policy": "connected algorithm/program/trace/code groups; no random per-step split",
        "prompt_version": PROMPT_VERSION,
        "harness_version": harness_version(config),
        "knowledge_version": knowledge_version(),
        "splits": {name: [e.id for e in rows] for name, rows in partitions.items()},
        "warnings": [
            "Fewer than three independent groups: validation and test are empty."
        ]
        if len(groups) < 3
        else [],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="For pipeline inspection only; unreviewed targets are not training-ready.",
    )
    args = parser.parse_args()
    examples = read_examples(args.path)
    if args.output:
        print(
            json.dumps(
                export_dataset(examples, args.output, args.include_drafts), indent=2
            )
        )
    else:
        print(
            json.dumps(
                {
                    "valid_examples": len(examples),
                    "approved": sum(e.review_status == "approved" for e in examples),
                }
            )
        )


if __name__ == "__main__":
    main()
