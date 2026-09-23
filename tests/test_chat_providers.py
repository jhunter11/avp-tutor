import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from providers import ProviderError, call_chat, strip_thinking


def test_ollama_uses_native_chat_without_vllm_extensions(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "local-test")
    response = httpx.Response(
        200,
        json={
            "message": {"content": "Saved in key."},
            "done_reason": "stop",
            "prompt_eval_count": 42,
            "eval_count": 7,
        },
        request=httpx.Request("POST", "http://localhost"),
    )
    with patch("providers.httpx.Client") as cls:
        cls.return_value.__enter__.return_value.post.return_value = response
        result = call_chat(
            [
                {"role": "system", "content": "Tutor"},
                {"role": "user", "content": "Why?"},
            ]
        )
        sent = cls.return_value.__enter__.return_value.post.call_args.kwargs["json"]
    assert sent["think"] is False
    assert sent["stream"] is False
    assert sent["model"] == "local-test"
    assert "chat_template_kwargs" not in json.dumps(sent)
    assert result.answer == "Saved in key."
    assert result.input_tokens == 42


def test_openai_keeps_system_and_history(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    response = MagicMock()
    response.choices[0].message.content = "Answer"
    response.choices[0].finish_reason = "stop"
    response.usage = None
    messages = [
        {"role": "system", "content": "Tutor"},
        {"role": "user", "content": "Why?"},
    ]
    with patch("providers.openai.OpenAI") as cls:
        cls.return_value.chat.completions.create.return_value = response
        result = call_chat(messages)
        sent = cls.return_value.chat.completions.create.call_args.kwargs
    assert sent["messages"] == messages
    assert "extra_body" not in sent
    assert result.provider == "openai"


def test_unknown_provider_fails_explicitly(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    monkeypatch.delenv("LLM_FALLBACK_PROVIDER", raising=False)
    with pytest.raises(ProviderError):
        call_chat([{"role": "user", "content": "hi"}])


def test_hidden_thinking_is_never_the_answer():
    assert strip_thinking("<think>private</think>Visible") == "Visible"
    assert strip_thinking("<think>unfinished") == ""


def test_fallback_reports_actual_provider(monkeypatch):
    from providers import Completion

    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("LLM_FALLBACK_PROVIDER", "openai")
    with patch(
        "providers._chat_provider",
        side_effect=[RuntimeError("down"), Completion("Answer", "openai", "test-api")],
    ):
        result = call_chat([{"role": "user", "content": "why"}])
    assert result.fallback_used
    assert result.provider == "openai"
    assert result.model == "test-api"


def test_busy_provider_fails_without_queueing(monkeypatch):
    from threading import BoundedSemaphore

    monkeypatch.setattr("providers._CHAT_SLOTS", BoundedSemaphore(0))
    with patch("providers._chat_provider") as provider:
        with pytest.raises(ProviderError, match="busy"):
            call_chat([{"role": "user", "content": "why"}])
    provider.assert_not_called()


def test_legacy_generation_shares_tutor_concurrency_limit(monkeypatch):
    from threading import BoundedSemaphore

    from providers import call_llm

    monkeypatch.setattr("providers._CHAT_SLOTS", BoundedSemaphore(0))
    with patch("providers._get_provider_fn") as provider:
        with pytest.raises(ProviderError, match="busy"):
            call_llm("Generate a function")
    provider.assert_not_called()


def test_legacy_failure_releases_shared_slot(monkeypatch):
    from threading import BoundedSemaphore

    from providers import call_llm

    slots = BoundedSemaphore(1)
    monkeypatch.setattr("providers._CHAT_SLOTS", slots)
    monkeypatch.delenv("LLM_FALLBACK_PROVIDER", raising=False)
    with patch("providers._get_provider_fn", side_effect=RuntimeError("unavailable")):
        with pytest.raises(RuntimeError, match="unavailable"):
            call_llm("Generate a function")
    assert slots.acquire(blocking=False)
    slots.release()


def test_gemini_uses_google_endpoint_and_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-google-key")
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")
    response = MagicMock()
    response.choices[0].message.content = "Google answer"
    response.choices[0].finish_reason = "stop"
    response.usage = None
    with patch("providers.openai.OpenAI") as cls:
        cls.return_value.chat.completions.create.return_value = response
        result = call_chat([{"role": "user", "content": "Explain this step"}])
        assert (
            cls.call_args.kwargs["base_url"]
            == "https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        assert cls.call_args.kwargs["api_key"] == "test-google-key"
    assert result.provider == "gemini"
    assert result.answer == "Google answer"
