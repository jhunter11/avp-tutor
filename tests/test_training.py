import json
from pathlib import Path

import pytest

from training.dataset import export_dataset, read_examples, validate_examples


def sample(id, algorithm, reviewed=True, code=""):
    return {
        "id": id,
        "algorithm": algorithm,
        "program_id": algorithm + "-v1",
        "trace_id": id,
        "provenance": "human-authored",
        "review_status": "approved" if reviewed else "draft",
        "reviewed_by": "reviewer" if reviewed else "",
        "request": {
            "question": "Explain " + id,
            "context": {"algorithm": algorithm, "code": code},
        },
        "answer": "A reviewed explanation of " + id,
        "expected_facts": ["Correct explanation"],
    }


def test_export_excludes_unreviewed_by_default(tmp_path):
    examples = [sample("one", "insertion_sort"), sample("two", "insertion_sort", False)]
    report = export_dataset(validate_examples(examples), tmp_path)
    assert report["exported"] == 1
    assert report["excluded_unreviewed"] == 1
    assert sum(len(p.read_text().splitlines()) for p in tmp_path.glob("*.jsonl")) == 1


def test_algorithm_groups_never_leak(tmp_path):
    rows = [
        sample(f"{algo}-{i}", algo)
        for algo in [
            "insertion_sort",
            "binary_search",
            "merge_sort",
            "bubble_sort",
            "selection_sort",
        ]
        for i in range(3)
    ]
    report = export_dataset(validate_examples(rows), tmp_path)
    seen = {}
    for partition, ids in report["splits"].items():
        for id in ids:
            algo = id.rsplit("-", 1)[0]
            assert algo not in seen or seen[algo] == partition
            seen[algo] = partition
    assert all(report["splits"].values())


def test_same_code_with_different_labels_stays_together(tmp_path):
    rows = [sample("a", "alpha", code="x = 1"), sample("b", "beta", code="x = 1")]
    report = export_dataset(validate_examples(rows), tmp_path)
    assert any(set(ids) == {"a", "b"} for ids in report["splits"].values())


def test_approved_requires_reviewer():
    row = sample("a", "sort")
    row["reviewed_by"] = ""
    with pytest.raises(ValueError):
        validate_examples([row])


def test_duplicate_id_rejected():
    row = sample("a", "sort")
    with pytest.raises(ValueError):
        validate_examples([row, row])


def test_export_matches_runtime_prompt_and_target(tmp_path):
    export_dataset(validate_examples([sample("a", "insertion_sort")]), tmp_path)
    record = json.loads((tmp_path / "train.jsonl").read_text().splitlines()[0])
    assert record["messages"][0]["role"] == "system"
    assert record["messages"][-1] == {
        "role": "assistant",
        "content": "A reviewed explanation of a",
    }
    assert "execution_context" in record["messages"][-2]["content"]


def test_seed_data_is_draft_and_benchmark_has_50_cases():
    rows = read_examples(Path("training/seed_examples.jsonl"))
    assert len(rows) >= 15
    assert all(row.review_status == "draft" for row in rows)
    assert len(read_examples(Path("training/benchmark.jsonl"))) == 50


def test_export_uses_same_history_aware_retrieval_as_runtime(tmp_path):
    from tutor.service import build_messages, sources_for_request

    example = sample("followup", "insertion_sort")
    example["request"]["history"] = [
        {"role": "user", "content": "Why did the key get overwritten?"},
        {"role": "assistant", "content": "Look at the saved variable."},
    ]
    example["request"]["question"] = "Was that a swap?"
    rows = validate_examples([example])
    export_dataset(rows, tmp_path)
    record = json.loads((tmp_path / "train.jsonl").read_text())
    assert record["messages"][:-1] == build_messages(
        rows[0].request, sources_for_request(rows[0].request)
    )


def test_export_freezes_one_harness_for_all_rows_and_manifest(tmp_path):
    from unittest.mock import patch

    from harness.config import harness_version, load_config

    config = load_config()
    rows = validate_examples([sample("a", "insertion_sort"), sample("b", "binary_search")])
    with (
        patch("training.dataset.load_config", return_value=config) as loader,
        patch("tutor.service.load_config", side_effect=AssertionError("Harness reloaded during export")),
    ):
        manifest = export_dataset(rows, tmp_path)
    loader.assert_called_once_with()
    assert manifest["harness_version"] == harness_version(config)


def test_evaluation_never_recaptures_consented_sessions(monkeypatch, tmp_path):
    from training import evaluate
    from tutor.models import TutorResponse

    row = sample("replay", "insertion_sort")
    row["request"]["feedback_consent"] = True
    dataset = tmp_path / "input.jsonl"
    dataset.write_text(json.dumps(row) + "\n")
    output = tmp_path / "report.jsonl"
    seen = []

    def answer(request):
        seen.append(request.feedback_consent)
        return TutorResponse(
            answer="A clue",
            sources=[],
            context_status="partial",
            warnings=[],
            provider="test",
            model="test",
            latency_ms=1,
            prompt_version="test",
            knowledge_version="test",
            harness_version="test",
            skill="hint.md",
        )

    monkeypatch.setattr(evaluate, "answer_question", answer)
    monkeypatch.setattr(
        "sys.argv", ["evaluate", "--dataset", str(dataset), "--output", str(output)]
    )
    evaluate.main()
    assert seen == [False]
