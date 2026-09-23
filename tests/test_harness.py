import json
from unittest.mock import patch

import pytest

from harness.config import harness_version, load_config
from harness.feedback import FeedbackStore
from harness.improve import propose_candidate
from providers import Completion
from tutor.models import TutorRequest
from tutor.service import answer_question, build_messages


def test_mode_skills_are_editable_and_used_by_prompt():
    request = TutorRequest(question="why", mode="hint")
    messages = build_messages(request, [])
    assert "guiding question" in messages[0]["content"]
    assert load_config().name == "baseline"


def test_inflight_answer_keeps_the_skill_and_version_it_used(monkeypatch, tmp_path):
    from pathlib import Path

    import harness.config as harness_config

    source_root = harness_config.ROOT
    (tmp_path / "skills").mkdir()
    for path in (source_root / "skills").glob("*.md"):
        (tmp_path / "skills" / path.name).write_text(path.read_text())
    baseline = tmp_path / "baseline.json"
    baseline.write_text((source_root / "configs" / "baseline.json").read_text())
    monkeypatch.setattr(harness_config, "ROOT", tmp_path)
    monkeypatch.setenv("HARNESS_CONFIG", str(baseline))
    config = load_config()
    original_version = harness_version(config)
    skill_path = Path(tmp_path / "skills" / config.skills["hint"])
    original_skill = skill_path.read_text()

    def finish_model_call(messages):
        assert original_skill in messages[0]["content"]
        skill_path.write_text("A changed skill for subsequent requests.")
        return Completion("Answer from original skill", "ollama", "test")

    with patch("tutor.service.call_chat", side_effect=finish_model_call):
        response = answer_question(TutorRequest(question="Why?", mode="hint"))
    assert response.harness_version == original_version
    assert harness_version(load_config()) != original_version


def test_invalid_harness_cannot_escape_skill_directory(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {"name": "bad", "retrieval_k": 3, "skills": {"hint": "../../secret.md"}}
        )
    )
    with pytest.raises(ValueError):
        load_config(path)


def test_feedback_requires_existing_interaction(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    with pytest.raises(KeyError):
        store.add_feedback("unknown", "too_much_answer", "")


def test_feedback_update_is_one_vote_per_interaction(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    id = store.record(
        {"question": "Why?"}, {"answer": "Because", "harness_version": "v1"}
    )
    store.add_feedback(id, "helpful", "")
    store.add_feedback(id, "too_much_answer", "Prefer a hint")
    rows = store.review_rows()
    assert len(rows) == 1
    assert rows[0]["rating"] == "too_much_answer"
    assert rows[0]["request"]["question"] == "Why?"


def test_no_consent_means_no_capture(monkeypatch, tmp_path):
    monkeypatch.setenv("FEEDBACK_ENABLED", "true")
    monkeypatch.setenv("FEEDBACK_DB_PATH", str(tmp_path / "feedback.sqlite3"))
    with patch(
        "tutor.service.call_chat", return_value=Completion("Answer", "ollama", "test")
    ):
        result = answer_question(TutorRequest(question="Why?"))
    assert result.interaction_id is None
    assert not (tmp_path / "feedback.sqlite3").exists()


def test_candidate_is_not_automatically_promoted(tmp_path):
    config = load_config()
    original = config.model_dump()
    report = propose_candidate([{"rating": "too_much_answer"}] * 4, config)
    assert report["status"] == "proposal"
    assert report["requires_review"] is True
    assert report["evidence"]["too_much_answer"] == 4
    assert config.model_dump() == original
    assert report["candidate"]["skills"]["hint"] == "hint-scaffolded.md"


def test_non_use_is_not_negative_answer_feedback(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")
    store.record_usage("offered", "insertion_sort")
    store.record_usage("dismissed", "insertion_sort")
    assert store.review_rows() == []
    assert store.usage_summary() == {"dismissed": 1, "offered": 1}


def test_opt_in_capture_and_feedback_api(monkeypatch, tmp_path):
    from starlette.testclient import TestClient

    from api.dependencies import limiter
    from api.main import app

    monkeypatch.setenv("FEEDBACK_ENABLED", "true")
    monkeypatch.setenv("FEEDBACK_DB_PATH", str(tmp_path / "feedback.sqlite3"))
    limiter.reset()
    with (
        patch(
            "tutor.service.call_chat",
            return_value=Completion("Answer", "ollama", "test"),
        ),
        TestClient(app) as client,
    ):
        response = client.post(
            "/api/tutor", json={"question": "Why?", "feedback_consent": True}
        )
        id = response.json()["interaction_id"]
        assert id
        assert (
            client.post(
                "/api/feedback", json={"interaction_id": id, "rating": "helpful"}
            ).status_code
            == 200
        )
        assert client.delete("/api/feedback/" + id).status_code == 204
        assert (
            client.post(
                "/api/feedback", json={"interaction_id": id, "rating": "helpful"}
            ).status_code
            == 404
        )


def test_loaded_harness_keeps_original_skill_text(monkeypatch, tmp_path):
    import shutil

    import harness.config as module

    shutil.copytree(module.ROOT / "skills", tmp_path / "skills")
    shutil.copytree(module.ROOT / "configs", tmp_path / "configs")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    config = module.load_config()
    version = module.harness_version(config)
    original = module.skill_text(config, "hint")
    (tmp_path / "skills" / config.skills["hint"]).write_text("Changed instruction")
    assert module.skill_text(config, "hint") == original
    assert module.harness_version(config) == version
    assert module.harness_version(module.load_config()) != version
