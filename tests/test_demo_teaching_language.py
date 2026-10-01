"""Realistic wording and counterexamples for the one-question teaching pack."""

import json

import pytest

from demo_v1.exercise import BUGGY, CORRECT
from demo_v1.service import AskRequest, prepare


def plan_for(question, code=BUGGY, values=None, target=7, history=None):
    request = AskRequest(
        code=code,
        values=[4, 7, 2, 7] if values is None else values,
        target=target,
        question=question,
        mode="explain",
        history=history or [],
    )
    messages, facts, *_ = prepare(request)
    return json.loads(messages[-1]["content"])["teaching_plan"], facts


@pytest.mark.parametrize(
    "question",
    [
        "Why do I get -1 when 7 is in the array?",
        "It works for the first item but not the second. What am I missing?",
        "Why does my result say not found even though the target is there?",
    ],
)
def test_runtime_evidence_guides_output_questions_without_naming_early_return(question):
    plan, _ = plan_for(question)
    assert plan["candidate_confusions"][0]["id"] == "early-return"
    assert plan["selection_basis"] == "execution evidence"
    assert plan["evidence"]["compared_indices"] == [0]


def test_returning_value_is_recognized_from_code_and_output_not_only_keywords():
    code = CORRECT.replace("return i", "return values[i]")
    plan, _ = plan_for("It returns 7 but the test expects 1. Why?", code)
    assert plan["candidate_confusions"][0]["id"] == "index-vs-value"
    assert plan["evidence"]["actual"] == 7
    assert plan["evidence"]["expected"] == 1


@pytest.mark.parametrize(
    "question",
    [
        "Why is the answer 1 instead of 2? I count the first position as 1.",
        "Is the first position numbered 0 or 1?",
    ],
)
def test_zero_based_indexing_has_specific_guidance_and_reference(question):
    plan, facts = plan_for(question, CORRECT)
    assert plan["candidate_confusions"][0]["id"] == "zero-based-indexing"
    assert "zero-based" in plan["explanation_method"]
    assert any("positions-and-values" in fact.id for fact in facts)


def test_array_length_definition_does_not_imply_a_student_misconception():
    plan, facts = plan_for("What does length(values) mean here?", CORRECT)
    assert plan["candidate_confusions"] == []
    assert plan["question_focus"] == "array length"
    assert any("array-length-and-bounds" in fact.id for fact in facts)


def test_completed_unsuccessful_search_is_not_called_an_early_return():
    code = CORRECT.replace("values[i] == target", "values[i] == -999")
    plan, _ = plan_for("Why do I get -1 when 7 is in the array?", code)
    assert plan["evidence"]["compared_indices"] == [0, 1, 2, 3]
    assert not any(c["id"] == "early-return" for c in plan["candidate_confusions"])


def test_contextual_followup_uses_recent_student_question_as_a_topic_only():
    history = [
        {"role": "user", "content": "Is the first position numbered 0 or 1?"},
        {"role": "assistant", "content": "The first position is numbered zero."},
    ]
    plan, _ = plan_for(
        "I still do not get it. Could you explain differently?",
        CORRECT,
        history=history,
    )
    assert plan["candidate_confusions"][0]["id"] == "zero-based-indexing"
    assert plan["selection_basis"] == "prior student question"


def test_a_short_loop_bound_does_not_imply_a_return_inside_the_loop():
    code = CORRECT.replace("i < length(values)", "i < length(values) - 1")
    plan, _ = plan_for("Why do I get -1 when 7 is in the array?", code, [4, 7])
    assert plan["evidence"]["compared_indices"] == [0]
    assert not any(c["id"] == "early-return" for c in plan["candidate_confusions"])


def test_short_circuit_does_not_count_an_array_read_that_never_happens():
    code = CORRECT.replace("values[i] == target", "false and values[i] == target")
    plan, _ = plan_for("Why do I get -1 when 7 is in the array?", code)
    assert plan["evidence"]["compared_indices"] == []


def test_computed_index_reads_come_from_execution_not_source_text_matching():
    code = BUGGY.replace("values[i]", "values[i + 0]")
    plan, _ = plan_for("Why do I get -1 when 7 is in the array?", code)
    assert plan["candidate_confusions"][0]["id"] == "early-return"
    assert plan["evidence"]["compared_indices"] == [0]
    assert plan["evidence"]["return_loop_depth"] == 1


def test_hidden_description_also_excludes_contract_references_and_requests_intent():
    request = AskRequest(
        code=BUGGY,
        values=[4, 7, 2],
        target=7,
        question="What might be wrong with my solution?",
        mode="debug",
        include_problem=False,
    )
    messages, facts, *_ = prepare(request)
    payload = json.loads(messages[-1]["content"])
    assert payload["teaching_plan"]["intent"] == "clarify intended output"
    assert "expected" not in payload["teaching_plan"]["evidence"]
    assert {fact.id for fact in facts} <= {
        "linear-search:return-and-loop-progress",
        "linear-search:array-length-and-bounds",
    }


@pytest.mark.parametrize(
    "question",
    [
        "Should duplicates return the first match?",
        "What about duplicate matches?",
        "Should I return the value or its position?",
    ],
)
def test_hidden_description_does_not_leak_contract_through_confusion_cards(question):
    request = AskRequest(
        code=CORRECT,
        values=[7, 4, 7],
        target=7,
        question=question,
        include_problem=False,
    )
    messages, *_ = prepare(request)
    plan = json.loads(messages[-1]["content"])["teaching_plan"]
    assert plan["candidate_confusions"] == []
    assert plan["intent"] == "clarify intended output"
    assert all("expects" not in observation for observation in plan["observations"])
