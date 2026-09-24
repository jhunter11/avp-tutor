import hashlib
import json
from unittest.mock import patch

from providers import Completion
from tutor.demo import build_trace
from tutor.evidence import inspect_evidence
from tutor.examples import select_examples
from tutor.models import TutorRequest
from tutor.service import answer_question, build_messages


def shift_frame():
    return next(
        f for f in build_trace([2, 7, 9, 4]) if f.recent_events[-1].kind == "shift"
    )


def test_evidence_hashes_exact_code_and_only_checks_supplied_facts():
    frame = shift_frame()
    result = inspect_evidence(frame)
    assert result.code_sha256 == hashlib.sha256(frame.code.encode()).hexdigest()
    assert result.status == "consistent"
    assert not result.execution_verified
    changed = frame.model_copy(update={"code": frame.code + "\n"})
    assert inspect_evidence(changed).code_sha256 != result.code_sha256


def test_conflicting_current_copy_is_detected_without_mutating_input():
    frame = shift_frame().model_copy(deep=True)
    frame.arrays["collection"][
        frame.recent_events[-1].details["destination_index"]
    ] = -42
    result = inspect_evidence(frame)
    assert result.status == "conflict"
    assert "copied_value" in " ".join(result.conflicts)
    assert -42 in frame.arrays["collection"]


def test_old_event_and_before_phase_are_not_treated_as_current_checks():
    frame = shift_frame().model_copy(deep=True)
    frame.current_line = 8
    assert inspect_evidence(frame).status == "not_checked"
    frame.current_line = 7
    frame.phase = "before"
    assert inspect_evidence(frame).status == "not_checked"


def test_multiple_arrays_without_identity_are_not_guessed():
    frame = shift_frame().model_copy(deep=True)
    frame.arrays["other"] = [99]
    result = inspect_evidence(frame)
    assert not any("destination" in check for check in result.checks)
    assert result.limitations


def test_examples_are_same_algorithm_bounded_and_not_execution_evidence():
    examples = select_examples(TutorRequest(question="why", context=shift_frame()))
    assert examples
    assert all(
        e.algorithm == "insertion_sort" and not e.execution_verified for e in examples
    )
    assert sum(len(e.code) for e in examples) <= 6000
    assert all(len(e.code_sha256) == 64 for e in examples)
    assert (
        select_examples(
            TutorRequest(question="sort", context={"algorithm": "unknown_sort"})
        )
        == []
    )


def test_explicit_strategy_and_provenance_reach_prompt_and_response():
    request = TutorRequest(question="why", strategy="comparison", context=shift_frame())
    with patch(
        "tutor.service.call_chat",
        return_value=Completion("A copy, not a swap.", "ollama", "test"),
    ) as call:
        response = answer_question(request)
    payload = json.loads(call.call_args.args[0][-1]["content"])
    assert payload["teaching_decision"]["strategy"] == "comparison"
    assert payload["code_examples"]
    assert response.teaching_decision.strategy == "comparison"
    assert response.evidence.code_sha256 == payload["evidence"]["code_sha256"]
    assert (
        response.prompt_sha256
        == hashlib.sha256(
            json.dumps(
                call.call_args.args[0], ensure_ascii=False, sort_keys=True
            ).encode()
        ).hexdigest()
    )


def test_conflict_selects_clarification_without_claiming_correctness():
    frame = shift_frame().model_copy(deep=True)
    frame.variables["key"] = -100
    response_request = TutorRequest(question="Explain this step", context=frame)
    payload = json.loads(build_messages(response_request, [])[-1]["content"])
    assert payload["teaching_decision"]["action"] == "clarify"
    assert payload["evidence"]["status"] == "conflict"


def test_concept_question_without_snapshot_can_still_be_explained():
    payload = json.loads(
        build_messages(TutorRequest(question="What is an invariant?"), [])[-1][
            "content"
        ]
    )
    assert payload["teaching_decision"]["action"] == "explain"


def test_unknown_citations_are_flagged_not_silently_verified():
    with patch(
        "tutor.service.call_chat",
        return_value=Completion("Fact [invented:source].", "ollama", "test"),
    ):
        response = answer_question(TutorRequest(question="why", context=shift_frame()))
    assert response.answer_checks.unknown_citations == ["invented:source"]
    assert not response.answer_checks.factual_accuracy_verified
    assert any("citation" in warning.lower() for warning in response.warnings)


def test_boolean_is_not_a_numeric_copy():
    frame = shift_frame().model_copy(deep=True)
    frame.recent_events[-1].details["copied_value"] = True
    frame.arrays["collection"] = [1] * len(frame.arrays["collection"])
    assert inspect_evidence(frame).status == "conflict"


def test_code_slice_is_not_a_citation():
    from tutor.service import check_answer

    assert check_answer("Inspect arr[1:3]", [], []).unknown_citations == []
