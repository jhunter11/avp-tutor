import json
from unittest.mock import patch

import pytest
from pydantic import ValidationError
from starlette.testclient import TestClient

from demo_v1.exercise import BUGGY, CORRECT
from demo_v1.memory import LearnerMemory
from demo_v1.retrieval import rank, retrieve_methods
from demo_v1.service import AskRequest, RunRequest, answer, prepare, run_code
from demo_v1.teaching import choose
from providers import Completion


def request(**kwargs):
    return AskRequest(
        code=BUGGY,
        values=[4, 7, 2, 7],
        target=7,
        question="Why does this fail later in the array?",
        **kwargs,
    )


def test_fixed_harness_exact_draft_and_actual_test_results_reach_model():
    messages, facts, methods, notes, run = prepare(request())
    payload = json.loads(messages[-1]["content"])
    assert payload["execution_context"]["code"] == BUGGY
    assert payload["execution_context"]["current_line"] == 7
    assert payload["demo_run"]["observations"][0]["actual"] == -1
    assert payload["demo_run"]["observations"][0]["expected"] == 1
    assert payload["teaching_plan"]["candidate_confusions"][0]["id"] == "early-return"
    assert facts and methods and notes == []
    assert {m["id"] for m in methods} == {
        "method:probe-misconception",
        "method:graduated-hints",
    }
    assert run["passed"] == 4
    assert "Do not show the corrected program" in messages[0]["content"]


def test_description_can_be_excluded_and_stale_step_rejected():
    payload = json.loads(prepare(request(include_problem=False))[0][-1]["content"])
    assert payload["problem_description"] is None
    assert all(
        "expected" not in r and "passed" not in r
        for r in payload["demo_run"]["observations"]
    )
    with pytest.raises(ValueError, match="step does not exist"):
        prepare(request(step=200))


def test_provider_neutral_answer_reports_actual_provider_and_fixed_versions():
    with patch(
        "demo_v1.service.call_chat",
        return_value=Completion(
            "Which indices were checked before line 7 returned?",
            "openrouter",
            "fixture-model",
        ),
    ):
        result = answer(request())
    assert result["provider"] == "openrouter"
    assert result["skill"] == "demo-first-match-hint.md"
    assert result["execution"]["passed"] == 4
    assert len(result["prompt_sha256"]) == 64
    assert result["memory_used"] == []


def test_demo_flags_inconsistent_reasoning_split_without_returning_private_text():
    with patch(
        "demo_v1.service.call_chat",
        return_value=Completion(
            "One clue.",
            "openrouter",
            "fixture-model",
            2500,
            300,
            reasoning_tokens=0,
            cached_input_tokens=1000,
            reasoning_characters=900,
        ),
    ):
        result = answer(request())
    assert result["input_tokens"] == 2500 and result["output_tokens"] == 300
    assert result["cached_input_tokens"] == 1000
    assert result["reasoning_split_available"] is False
    assert "reasoning_characters" not in result


@pytest.mark.parametrize(
    "question,confusion",
    [
        ("Why does it return early?", "early-return"),
        ("Do I return the value or the index?", "index-vs-value"),
        ("What about duplicate matches?", "duplicates"),
        ("What causes an off-by-one bound error?", "loop-bounds"),
        ("What happens for empty input?", "empty-input"),
        ("Why use a not found result?", "absent-target"),
        ("Does the loop increment make progress?", "loop-progress"),
    ],
)
def test_teaching_pack_maps_question_to_candidate_and_explanation(question, confusion):
    req = AskRequest(code=CORRECT, values=[1, 2], target=2, question=question)
    plan = choose(req, run_code(req)["cases"][0])
    assert plan["candidate_confusions"][0]["id"] == confusion
    assert plan["candidate_confusions"][0]["impact"]
    assert plan["explanation_method"]
    assert "hypotheses" in plan["limits"]


def test_vectors_rank_method_cards_and_unknown_terms_do_not_force_retrieval():
    assert (
        retrieve_methods("hint misconception reasoning")[0]["id"]
        == "method:probe-misconception"
    )
    assert rank("zzqxv", [{"id": "a", "text": "loop return index"}]) == []


def test_notes_persist_delete_and_remain_untrusted_optional_context(tmp_path):
    memory = LearnerMemory(tmp_path / "learner.sqlite3")
    memory.add("I confuse a return with continuing the loop.")
    note = memory.notes()[0]
    assert LearnerMemory(memory.path).notes()[0]["id"] == note["id"]
    req = request(use_memory=True)
    payload = json.loads(prepare(req, memory)[0][-1]["content"])
    assert payload["learner_notes"][0]["text"] == note["text"]
    assert not prepare(request(), memory)[3]
    with pytest.raises(ValueError, match="credentials"):
        memory.add("api_key=not-a-real-key")
    with pytest.raises(ValueError, match="credentials"):
        memory.add("AIza" + "x" * 35)
    assert memory.delete(note["id"]) and memory.notes() == []


def test_strict_input_rejects_boolean_as_integer():
    with pytest.raises(ValidationError):
        RunRequest(code=CORRECT, values=[True], target=1)


def test_demo_api_isolated_and_local_mutations_require_session(monkeypatch, tmp_path):
    monkeypatch.setenv("AVP_DEMO_MEMORY_PATH", str(tmp_path / "learner.sqlite3"))
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    from demo_v1.app import app

    with TestClient(app) as client:
        state = client.get("/demo/api/status").json()
        headers = {"X-Demo-Token": state["token"]}
        assert client.get("/").status_code == 200
        assert (
            client.get("/demo/api/status", headers={"host": "evil.example"}).status_code
            == 403
        )
        assert (
            client.post("/demo/api/run", json=request().model_dump()).status_code == 403
        )
        assert (
            client.post(
                "/demo/api/run",
                headers={**headers, "Origin": "https://evil.example"},
                json={},
            ).status_code
            == 403
        )
        body = RunRequest(code=CORRECT, values=[1, 2], target=2).model_dump()
        assert (
            client.post("/demo/api/run", headers=headers, json=body).json()["passed"]
            == 6
        )
        assert (
            client.post(
                "/demo/api/ask", headers=headers, json=request().model_dump()
            ).status_code
            == 503
        )
        assert (
            client.post(
                "/demo/api/notes",
                headers=headers,
                json={"text": "Remember return ends the function."},
            ).status_code
            == 200
        )
        notes = client.get("/demo/api/notes").json()
        assert (
            client.delete(
                "/demo/api/notes/" + notes[0]["id"], headers=headers
            ).status_code
            == 200
        )
        assert client.post("/api/feedback", headers=headers, json={}).status_code in {
            404,
            405,
        }
        assert (
            client.post(
                "/demo/api/notes", headers=headers, content="x" * 70000
            ).status_code
            == 413
        )
