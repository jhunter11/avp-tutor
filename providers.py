"""Bounded text-chat adapters selected through provider profiles."""

import os
import re
import sys
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from threading import BoundedSemaphore, Lock
from typing import Callable

import anthropic
import httpx
import openai

from llm_config import (
    ConfigurationError,
    configured,
    credential,
    provider_name,
    resolve_profile,
)


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
    return provider_name()


def provider_model(provider: str | None = None) -> str:
    try:
        return resolve_profile(provider).model
    except ConfigurationError:
        return ""


def is_provider_configured() -> bool:
    try:
        return configured(resolve_profile())
    except ConfigurationError:
        return False


_PRICE_LOCK = Lock()
_FREE_MODELS = {}


def _require_free_openrouter(model):
    with _PRICE_LOCK:
        if _FREE_MODELS.get(model, 0) > time.monotonic():
            return
        try:
            response = httpx.get("https://openrouter.ai/api/v1/models", timeout=20)
            response.raise_for_status()
            entry = next((m for m in response.json()["data"] if m["id"] == model), None)
            prices = entry["pricing"] if entry else {}
            if (not prices or any(Decimal(str(prices[k])) != 0 for k in ("prompt", "completion"))
                    or any(Decimal(str(v)) != 0 for k, v in prices.items() if k in {"request", "image", "audio", "input_audio"})):
                raise ProviderError("The selected OpenRouter model is not cataloged with zero prices.")
        except ProviderError:
            raise
        except (httpx.HTTPError, KeyError, TypeError, ValueError, InvalidOperation) as error:
            raise ProviderError("Cannot verify zero OpenRouter prices. No model request was sent.") from error
        _FREE_MODELS[model] = time.monotonic() + 300


def _limits():
    return max(1, min(float(os.environ.get("LLM_TIMEOUT_SECONDS", "90")), 180)), max(
        64, min(int(os.environ.get("LLM_MAX_TOKENS", "700")), 4096)
    )


def _chat_provider(name: str, messages: list[dict]) -> Completion:
    timeout, max_tokens = _limits()
    try:
        profile = resolve_profile(name)
    except ConfigurationError as error:
        raise ProviderError(str(error)) from None
    model = profile.model
    if not model:
        raise ProviderError(
            f"Set {name.upper()}_MODEL to a model available in your account."
        )
    if profile.adapter == "ollama":
        base = profile.base_url.rstrip("/")
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
    elif profile.adapter == "anthropic":
        key = credential(profile)
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not set.")
        client = anthropic.Anthropic(api_key=key, base_url=profile.base_url, timeout=timeout, max_retries=0)
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
    elif profile.adapter in {"openai-compatible", "openrouter"}:
        key = credential(profile)
        if not key and profile.require_key:
            raise ProviderError(f"{profile.api_key_env} is not set.")
        key = key or "local"
        free_only = os.environ.get("OPENROUTER_FREE_ONLY", "true").lower() != "false"
        if profile.adapter == "openrouter" and free_only:
            _require_free_openrouter(model)
        base = profile.base_url
        client = openai.OpenAI(
            base_url=base, api_key=key, timeout=timeout, max_retries=0
        )
        try:
            kwargs = {"model": model, "messages": messages}
            kwargs[profile.token_parameter] = max_tokens
            if profile.adapter == "openrouter":
                routing = {"allow_fallbacks": False}
                if free_only:
                    routing["max_price"] = {"prompt": 0, "completion": 0, "request": 0, "image": 0, "audio": 0}
                kwargs["extra_body"] = {"provider": routing}
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
            "Unknown provider adapter."
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
        if _known_provider(fallback) and fallback != primary:
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


def _call_openrouter(prompt: str) -> str:
    return _chat_provider("openrouter", [{"role": "user", "content": prompt}]).answer


def _call_compatible(prompt: str) -> str:
    return _chat_provider("compatible", [{"role": "user", "content": prompt}]).answer


def _known_provider(name):
    if not name:
        return False
    try:
        resolve_profile(name)
        return True
    except ConfigurationError:
        return False


_PROVIDER_FN_NAMES = {
    "gemini": "_call_gemini",
    "anthropic": "_call_anthropic",
    "vllm": "_call_vllm",
    "ollama": "_call_ollama",
    "openai": "_call_openai",
    "openrouter": "_call_openrouter",
    "compatible": "_call_compatible",
}


def _get_provider_fn(name: str) -> Callable[[str], str]:
    if name not in _PROVIDER_FN_NAMES:
        if _known_provider(name):
            return lambda prompt: _chat_provider(name, [{"role": "user", "content": prompt}]).answer
        raise ProviderError("Unknown LLM_PROVIDER.")
    return getattr(sys.modules[__name__], _PROVIDER_FN_NAMES[name])


def _dispatch_llm(prompt: str) -> str:
    provider = get_provider_name()
    fallback = os.environ.get("LLM_FALLBACK_PROVIDER", "")
    try:
        return _get_provider_fn(provider)(prompt)
    except Exception:
        if _known_provider(fallback) and fallback != provider:
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
