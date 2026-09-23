"""Bounded chat providers. Local inference is the default; cloud fallback is opt-in."""

import os
import re
import sys
from dataclasses import dataclass
from threading import BoundedSemaphore
from typing import Callable

import anthropic
import httpx
import openai


class ProviderError(RuntimeError):
    """Public, credential-free provider failure."""


@dataclass
class Completion:
    answer: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    truncated: bool = False
    fallback_used: bool = False


def strip_thinking(text: str) -> str:
    text = re.sub(r"^\s*<think>.*?</think>\s*", "", text or "", flags=re.DOTALL)
    if text.lstrip().startswith("<think>"):
        return ""
    return text.strip()


def get_provider_name() -> str:
    return os.environ.get("LLM_PROVIDER", "ollama").lower()


def provider_model(provider: str | None = None) -> str:
    name = provider or get_provider_name()
    defaults = {
        "ollama": "qwen3:8b",
        "vllm": "local-model",
        "anthropic": "",
        "openai": "",
        "gemini": "",
    }
    return os.environ.get(f"{name.upper()}_MODEL", defaults.get(name, ""))


def is_provider_configured() -> bool:
    name = get_provider_name()
    if name == "ollama":
        return bool(provider_model(name))
    if name == "vllm":
        return bool(os.environ.get("VLLM_BASE_URL") and provider_model(name))
    if name == "gemini":
        return bool(
            (os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
            and provider_model(name)
        )
    if name in {"anthropic", "openai"}:
        return bool(os.environ.get(f"{name.upper()}_API_KEY") and provider_model(name))
    return False


def _limits():
    return max(1, min(float(os.environ.get("LLM_TIMEOUT_SECONDS", "90")), 180)), max(
        64, min(int(os.environ.get("LLM_MAX_TOKENS", "700")), 4096)
    )


def _chat_provider(name: str, messages: list[dict]) -> Completion:
    timeout, max_tokens = _limits()
    model = provider_model(name)
    if not model:
        raise ProviderError(
            f"Set {name.upper()}_MODEL to a model available in your account."
        )
    if name == "ollama":
        base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                f"{base}/api/chat",
                json={
                    "model": model,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": {
                        "temperature": 0.2,
                        "num_predict": max_tokens,
                        "num_ctx": 16384,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
        result = Completion(
            data["message"]["content"],
            name,
            model,
            data.get("prompt_eval_count"),
            data.get("eval_count"),
            data.get("done_reason") == "length",
        )
    elif name == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not set.")
        client = anthropic.Anthropic(api_key=key, timeout=timeout, max_retries=0)
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system="\n".join(
                    m["content"] for m in messages if m["role"] == "system"
                ),
                messages=[m for m in messages if m["role"] != "system"],
            )
            result = Completion(
                "\n".join(
                    b.text
                    for b in response.content
                    if getattr(b, "type", "text") == "text"
                ),
                name,
                model,
                response.usage.input_tokens,
                response.usage.output_tokens,
                response.stop_reason == "max_tokens",
            )
        finally:
            client.close()
    elif name in {"vllm", "openai", "gemini"}:
        key = os.environ.get(
            f"{name.upper()}_API_KEY", "local" if name == "vllm" else ""
        )
        if name == "gemini":
            key = os.environ.get("GEMINI_API_KEY") or os.environ.get(
                "GOOGLE_API_KEY", ""
            )
        if not key:
            raise ProviderError(f"{name.upper()}_API_KEY is not set.")
        base = os.environ.get(
            f"{name.upper()}_BASE_URL",
            "http://localhost:8001/v1"
            if name == "vllm"
            else "https://api.openai.com/v1",
        )
        if name == "gemini":
            base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        client = openai.OpenAI(
            base_url=base, api_key=key, timeout=timeout, max_retries=0
        )
        try:
            kwargs = {"model": model, "messages": messages}
            kwargs[
                "max_tokens" if name in {"vllm", "gemini"} else "max_completion_tokens"
            ] = max_tokens
            # Model-specific sampling extensions are deliberately not sent to all servers.
            response = client.chat.completions.create(**kwargs)
            usage = response.usage
            result = Completion(
                response.choices[0].message.content or "",
                name,
                model,
                usage.prompt_tokens if usage else None,
                usage.completion_tokens if usage else None,
                response.choices[0].finish_reason == "length",
            )
        finally:
            client.close()
    else:
        raise ProviderError(
            "Unknown LLM_PROVIDER; use ollama, gemini, openai, anthropic, or vllm."
        )
    result.answer = strip_thinking(result.answer)
    if not result.answer:
        raise ProviderError(
            "The model returned no visible answer. Try a larger output limit or a different model."
        )
    return result


def _dispatch_chat(messages: list[dict]) -> Completion:
    primary = get_provider_name()
    fallback = os.environ.get("LLM_FALLBACK_PROVIDER", "").lower()
    try:
        return _chat_provider(primary, messages)
    except Exception as exc:
        if fallback in _PROVIDER_FN_NAMES and fallback != primary:
            try:
                result = _chat_provider(fallback, messages)
                result.fallback_used = True
                return result
            except Exception:
                pass
        if isinstance(exc, ProviderError):
            raise exc
        raise ProviderError(
            "The configured model is unavailable. Check the model name and server configuration."
        ) from exc


# Preserve upstream string-generation entry points for existing integrations.
def _call_anthropic(prompt: str) -> str:
    return _chat_provider("anthropic", [{"role": "user", "content": prompt}]).answer


def _call_vllm(prompt: str) -> str:
    return _chat_provider("vllm", [{"role": "user", "content": prompt}]).answer


def _call_ollama(prompt: str) -> str:
    return _chat_provider("ollama", [{"role": "user", "content": prompt}]).answer


def _call_openai(prompt: str) -> str:
    return _chat_provider("openai", [{"role": "user", "content": prompt}]).answer


def _call_gemini(prompt: str) -> str:
    return _chat_provider("gemini", [{"role": "user", "content": prompt}]).answer


_PROVIDER_FN_NAMES = {
    "gemini": "_call_gemini",
    "anthropic": "_call_anthropic",
    "vllm": "_call_vllm",
    "ollama": "_call_ollama",
    "openai": "_call_openai",
}


def _get_provider_fn(name: str) -> Callable[[str], str]:
    if name not in _PROVIDER_FN_NAMES:
        raise ProviderError("Unknown LLM_PROVIDER.")
    return getattr(sys.modules[__name__], _PROVIDER_FN_NAMES[name])


def _dispatch_llm(prompt: str) -> str:
    provider = get_provider_name()
    fallback = os.environ.get("LLM_FALLBACK_PROVIDER", "")
    try:
        return _get_provider_fn(provider)(prompt)
    except Exception:
        if fallback in _PROVIDER_FN_NAMES and fallback != provider:
            return _get_provider_fn(fallback)(prompt)
        raise


_CHAT_SLOTS = BoundedSemaphore(2)


def call_chat(messages: list[dict]) -> Completion:
    """Bound concurrent model work per process, including disconnected clients."""
    if not _CHAT_SLOTS.acquire(blocking=False):
        raise ProviderError("The tutor is busy. Try again shortly.")
    try:
        return _dispatch_chat(messages)
    finally:
        _CHAT_SLOTS.release()


def call_llm(prompt: str) -> str:
    if not _CHAT_SLOTS.acquire(blocking=False):
        raise ProviderError("The tutor is busy. Try again shortly.")
    try:
        return _dispatch_llm(prompt)
    finally:
        _CHAT_SLOTS.release()
