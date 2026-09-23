"""Scaffold a reviewable candidate from explicit feedback, never promote it."""

import argparse
import json
from collections import Counter
from pathlib import Path

from harness.config import harness_version, load_config
from harness.feedback import FeedbackStore


def propose_candidate(rows, config):
    counts = Counter(row["rating"] for row in rows)
    candidate = config.model_dump()
    candidate["name"] = config.name + "-candidate"
    changes = []
    if counts["too_much_answer"] >= 3:
        candidate["skills"]["hint"] = "hint-scaffolded.md"
        changes.append(
            "Evaluate the more constrained hint skill on hint and follow-up cases."
        )
    if counts["missing_context"] >= 3:
        candidate["retrieval_k"] = min(6, config.retrieval_k + 1)
        changes.append(
            "Test one additional teaching note; first inspect whether missing runtime state caused the reports, since retrieval cannot restore that state."
        )
    if counts["incorrect"]:
        changes.append(
            "Review reported incorrect answers against the interpreter before creating corrected examples."
        )
    return {
        "status": "proposal",
        "requires_review": True,
        "baseline_version": harness_version(config),
        "evidence": dict(counts),
        "candidate": candidate,
        "proposed_checks": changes,
        "limitations": [
            "Feedback is self-selected and unverified.",
            "Usage/dismissal is not an answer-quality label.",
            "No active config or model weights were changed.",
            "Replay baseline and candidate on separate evaluation cases and have an instructor review regressions before promotion.",
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("artifacts/feedback.sqlite3"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/candidate"))
    args = parser.parse_args()
    if not args.db.exists():
        parser.error(
            "Feedback database does not exist; collect consented feedback first."
        )
    store = FeedbackStore(args.db)
    report = propose_candidate(store.review_rows(), load_config())
    report["usage_counts_not_quality_labels"] = store.usage_summary()
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "proposal.json").write_text(json.dumps(report, indent=2) + "\n")
    (args.output / "harness.json").write_text(
        json.dumps(report["candidate"], indent=2) + "\n"
    )
    print("Wrote a candidate and evidence report. Nothing was promoted or trained.")


if __name__ == "__main__":
    main()
