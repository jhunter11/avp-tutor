import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from llm_config import (
    ConfigurationError,
    credential,
    profiles,
    public_status,
    resolve_profile,
)
from providers import ProviderError, call_chat


def completion():
    response = MagicMock()
    response.choices[0].message.content = "The return stops the loop before the next item."
    response.choices[0].finish_reason = "stop"
    response.usage = None
    return response


def catalog(model, price="0"):
    return httpx.Response(200, json={"data": [{"id": model, "pricing": {"prompt": price, "completion": price}}]}, request=httpx.Request("GET", "https://openrouter.ai/api/v1/models"))


def test_openrouter_is_default_and_public_config_excludes_key(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "private-test-marker")
    status = public_status()
    assert status["provider"] == "openrouter" and status["configured"]
    assert status["model"] == "stealth/space-bunny-alpha"
    assert "private-test-marker" not in json.dumps(status)


@pytest.mark.parametrize("model,price", [("free-test", "0"), ("paid-test", "0.001")])
def test_openrouter_enforces_free_catalog_and_request_prices(monkeypatch, model, price):
    import providers
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_MODEL", model)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-router-key")
    monkeypatch.delenv("LLM_FALLBACK_PROVIDER", raising=False)
    monkeypatch.delenv("OPENROUTER_FREE_ONLY", raising=False)
    monkeypatch.setattr(providers, "_FREE_MODELS", {})
    with patch("providers.httpx.get", return_value=catalog(model, price)), patch("providers.openai.OpenAI") as client:
        client.return_value.chat.completions.create.return_value = completion()
        if price != "0":
            with pytest.raises(ProviderError, match="zero prices"):
                call_chat([{"role": "user", "content": "Why does it stop?"}])
            client.assert_not_called()
        else:
            answer = call_chat([{"role": "user", "content": "Why does it stop?"}])
            sent = client.return_value.chat.completions.create.call_args.kwargs
            assert client.call_args.kwargs["base_url"] == "https://openrouter.ai/api/v1"
            assert sent["extra_body"]["provider"]["allow_fallbacks"] is False
            assert all(price == 0 for price in sent["extra_body"]["provider"]["max_price"].values())
            assert answer.provider == "openrouter"


def test_catalog_failure_never_sends_a_completion(monkeypatch):
    import providers
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-router-key")
    monkeypatch.delenv("LLM_FALLBACK_PROVIDER", raising=False)
    monkeypatch.setattr(providers, "_FREE_MODELS", {})
    with patch("providers.httpx.get", side_effect=httpx.ConnectError("offline")), patch("providers.openai.OpenAI") as client:
        with pytest.raises(ProviderError, match="Cannot verify"):
            call_chat([{"role": "user", "content": "Why?"}])
        client.assert_not_called()


def test_gemini_can_be_selected_later_without_copying_a_router_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("OPENROUTER_API_KEY", "router-only")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_MODEL", "future-test-model")
    assert not public_status()["configured"]
    assert not credential(resolve_profile())
    monkeypatch.setenv("GOOGLE_API_KEY", "google-test")
    assert public_status()["configured"]
    monkeypatch.setenv("GEMINI_BASE_URL", "https://wrong.example/v1")
    assert resolve_profile().base_url == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_custom_compatible_provider_changes_without_source_edits(tmp_path, monkeypatch):
    path = tmp_path / "profiles.json"
    profile = dict(profiles()["compatible"].__dict__)
    profile.pop("name")
    profile.update(base_url="https://gateway.example/v1", api_key_env="TEAM_GATEWAY_KEY", model="team-model", require_key=True)
    path.write_text(json.dumps({"version": 1, "providers": {"team-gateway": profile}}))
    monkeypatch.setenv("LLM_PROVIDERS_FILE", str(path))
    monkeypatch.setenv("LLM_PROVIDER", "team-gateway")
    monkeypatch.setenv("TEAM_GATEWAY_KEY", "team-test-key")
    monkeypatch.setenv("TEAM_GATEWAY_MODEL", "override-model")
    with patch("providers.openai.OpenAI") as client:
        client.return_value.chat.completions.create.return_value = completion()
        response = call_chat([{"role": "user", "content": "Explain this step"}])
        assert client.call_args.kwargs["api_key"] == "team-test-key"
        assert client.call_args.kwargs["base_url"] == "https://gateway.example/v1"
    assert response.provider == "team-gateway" and response.model == "override-model"


def test_profile_rejects_literal_credentials_and_secret_endpoint(tmp_path, monkeypatch):
    raw = dict(profiles()["compatible"].__dict__)
    raw.pop("name")
    raw["api_key"] = "private-test-marker"
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"version": 1, "providers": {"compatible": raw}}))
    monkeypatch.setenv("LLM_PROVIDERS_FILE", str(path))
    with pytest.raises(ConfigurationError) as error:
        profiles()
    assert "private-test-marker" not in str(error.value)
    raw.pop("api_key")
    raw["base_url"] = "https://user:private-test-marker@gateway.example/v1"
    path.write_text(json.dumps({"version": 1, "providers": {"compatible": raw}}))
    with pytest.raises(ConfigurationError) as error:
        resolve_profile("compatible")
    assert "private-test-marker" not in str(error.value)
