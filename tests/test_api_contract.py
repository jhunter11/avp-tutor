from unittest.mock import patch

from starlette.testclient import TestClient

from api.cache import TTLCache
from providers import Completion


def test_legacy_message_alias_and_query_both_work(client):
    for key in ("message", "query"):
        response = client.post("/api/generate", json={key: "add two numbers"})
        assert response.status_code == 200
        assert response.json()["validation"]["syntax_valid"]
        assert not response.json()["validation"]["execution_verified"]


def test_case_sensitive_code_is_not_cache_collapsed():
    cache = TTLCache()
    cache.set("Explain True", "boolean")
    assert cache.get("Explain true") is None


def test_oversized_body_is_rejected_before_provider_call():
    from api.main import app

    with patch("tutor.service.call_chat") as call, TestClient(app) as client:
        response = client.post("/api/tutor", json={"question": "x" * 140000})
    assert response.status_code == 413
    call.assert_not_called()


def test_unknown_context_fields_rejected():
    from api.main import app

    with TestClient(app) as client:
        response = client.post(
            "/api/context/validate",
            json={"algorithm": "sort", "secret_unknown_field": "x"},
        )
    assert response.status_code == 422


def test_forwarded_ip_is_not_trusted_by_default(monkeypatch):
    from starlette.requests import Request

    from api.dependencies import client_ip

    monkeypatch.delenv("TRUSTED_PROXY_IPS", raising=False)
    request = Request(
        {
            "type": "http",
            "client": ("192.0.2.1", 123),
            "headers": [(b"x-real-ip", b"203.0.113.3")],
        }
    )
    assert client_ip(request) == "192.0.2.1"


def test_different_snapshots_with_same_question_each_reach_model():
    from api.dependencies import limiter
    from api.main import app

    limiter.reset()
    with (
        patch(
            "tutor.service.call_chat",
            return_value=Completion("Answer", "ollama", "test"),
        ) as call,
        TestClient(app) as client,
    ):
        for value in [3, 7]:
            assert (
                client.post(
                    "/api/tutor",
                    json={
                        "question": "What is key?",
                        "context": {"variables": {"key": value}},
                    },
                ).status_code
                == 200
            )
    assert call.call_count == 2
    assert '"key": 3' in call.call_args_list[0].args[0][-1]["content"]
    assert '"key": 7' in call.call_args_list[1].args[0][-1]["content"]


def test_demo_bounds_and_invalid_input():
    from api.main import app

    with TestClient(app) as client:
        for values in ["NaN", "1,2,", "1000", ",".join(["1"] * 25)]:
            assert (
                client.get(
                    "/api/demo/insertion-sort", params={"values": values}
                ).status_code
                == 422
            )
        assert (
            client.get("/api/demo/insertion-sort", params={"values": ""}).json()[
                "frames"
            ][-1]["arrays"]["collection"]
            == []
        )


def test_committed_integration_schema_matches_backend():
    import json
    from pathlib import Path

    from api.main import app

    assert json.loads(Path("integrations/openapi.json").read_text()) == app.openapi()
