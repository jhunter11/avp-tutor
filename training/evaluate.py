"""Replay the same cases against any configured provider; no model-based grading."""

import argparse
import json
import re
from pathlib import Path

from dotenv import load_dotenv

from training.dataset import read_examples
from tutor.service import answer_question


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", type=Path, default=Path("training/benchmark.jsonl")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/evaluation.jsonl")
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="0 runs all cases; each case makes a model request",
    )
    parser.add_argument(
        "--harness",
        type=Path,
        help="Evaluate a candidate config without changing the server",
    )
    parser.add_argument(
        "--env-file", type=Path, help="Load provider credentials from this local file"
    )
    args = parser.parse_args()
    if args.harness:
        import os

        os.environ["HARNESS_CONFIG"] = str(args.harness.resolve())
    if args.limit < 0:
        parser.error("limit must be nonnegative")
    load_dotenv(args.env_file)
    examples = read_examples(args.dataset)
    if args.limit:
        examples = examples[: args.limit]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    errors = 0
    with args.output.open("w") as output:
        for example in examples:
            row = {
                "id": example.id,
                "expected_facts": example.expected_facts,
                "reference_answer": example.answer,
                "review": {
                    "state_accuracy": None,
                    "algorithm_correctness": None,
                    "teaching_usefulness": None,
                },
            }
            try:
                # Replaying a consented session is not a new learner interaction.
                result = answer_question(
                    example.request.model_copy(update={"feedback_consent": False})
                )
                row["response"] = result.model_dump()
                cited = set(re.findall(r"\[([^\[\]]+:[^\[\]]+)\]", result.answer))
                allowed = {s.id for s in result.sources}
                row["automated_flags"] = {
                    "unknown_citations": sorted(cited - allowed),
                    "empty_answer": not result.answer.strip(),
                    "over_300_words": len(result.answer.split()) > 300,
                }
            except Exception as exc:
                # Do not write SDK details or keys into a dataset report.
                row["error"] = type(exc).__name__
                errors += 1
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
            output.flush()
            print(
                f"{example.id}: {'error' if 'error' in row else 'recorded for review'}",
                flush=True,
            )
    print(
        f"Wrote {len(examples)} cases to {args.output}. {errors} request errors. Human rubric scores remain unfilled; this is not an accuracy score."
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
