"""Small text-chat profiles. Public configuration names credentials; it never stores them."""

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
DEFAULT_PROFILES = ROOT / "config" / "providers.json"
ADAPTERS = {"openrouter", "openai-compatible", "anthropic", "ollama"}
FIELDS = {"adapter", "base_url", "api_key_env", "model", "token_parameter", "require_key"}


class ConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderProfile:
    name: str
    adapter: str
    base_url: str
    api_key_env: str
    model: str
    token_parameter: str
    require_key: bool

    def public(self):
        return {"provider": self.name, "adapter": self.adapter,
                "model": self.model, "endpoint": self.base_url, "credential_variable": self.api_key_env}


def provider_name(environ=None):
    env = os.environ if environ is None else environ
    return env.get("LLM_PROVIDER", "openrouter").strip().lower()


def profiles(environ=None):
    env = os.environ if environ is None else environ
    path = Path(env.get("LLM_PROVIDERS_FILE") or DEFAULT_PROFILES)
    try:
        if path.stat().st_size > 65536:
            raise ConfigurationError("Provider configuration exceeds 64 KiB.")
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigurationError("Cannot read a valid provider configuration file.") from error
    if (not isinstance(data, dict) or set(data) != {"version", "providers"}
            or type(data["version"]) is not int or data["version"] != 1 or not isinstance(data["providers"], dict)
            or not 1 <= len(data["providers"]) <= 32):
        raise ConfigurationError("Use a version 1 file with 1 to 32 provider profiles.")
    result = {}
    for name, raw in data["providers"].items():
        if not re.fullmatch(r"[a-z][a-z0-9_-]{0,40}", name):
            raise ConfigurationError("Provider names must be short lowercase identifiers.")
        if not isinstance(raw, dict) or set(raw) != FIELDS:
            raise ConfigurationError("Profiles need adapter, base_url, api_key_env, model, token_parameter, and require_key. Credential values are not allowed.")
        if (type(raw["require_key"]) is not bool
                or any(not isinstance(raw[k], str) for k in FIELDS - {"require_key"})
                or raw["adapter"] not in ADAPTERS or raw["token_parameter"] not in {"max_tokens", "max_completion_tokens"}):
            raise ConfigurationError("Invalid provider adapter or profile field type.")
        if raw["api_key_env"] and not re.fullmatch(r"[A-Z_][A-Z0-9_]{0,80}", raw["api_key_env"]):
            raise ConfigurationError("Use a credential environment-variable name, not a credential value.")
        if len(raw["model"]) > 160 or len(raw["base_url"]) > 500:
            raise ConfigurationError("Provider model or endpoint is too long.")
        result[name] = ProviderProfile(name=name, **raw)
    return result


def resolve_profile(name=None, environ=None):
    env = os.environ if environ is None else environ
    name = name or provider_name(env)
    profile = profiles(env).get(name)
    if profile is None:
        raise ConfigurationError("Unknown LLM_PROVIDER. Select a configured profile.")
    prefix = name.upper().replace("-", "_")
    model = env.get(f"{prefix}_MODEL", profile.model)
    base = env.get(f"{prefix}_BASE_URL", profile.base_url)
    # Native named credentials stay on the documented service endpoint.
    if name in {"gemini", "openrouter"}:
        expected_adapter = "openai-compatible" if name == "gemini" else "openrouter"
        if profile.adapter != expected_adapter or profile.api_key_env != f"{name.upper()}_API_KEY" or not profile.require_key:
            raise ConfigurationError("Named Gemini and OpenRouter profiles must keep their service adapter and credential variable.")
        base = profile.base_url
        expected = "generativelanguage.googleapis.com" if name == "gemini" else "openrouter.ai"
        try:
            hostname = urlsplit(base).hostname
        except ValueError:
            raise ConfigurationError("Invalid provider endpoint URL.") from None
        if hostname != expected:
            raise ConfigurationError("Use the documented endpoint for this named provider. Use a separate compatible profile for another service.")
    try:
        parsed = urlsplit(base)
        _ = parsed.port
    except ValueError:
        raise ConfigurationError("Invalid provider endpoint URL.") from None
    if parsed.scheme not in {"https", "http"} or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ConfigurationError("Use an HTTP(S) endpoint without credentials, query parameters, or fragments.")
    if parsed.scheme == "http" and (name == "gemini" or profile.adapter in {"openrouter", "anthropic"}):
        raise ConfigurationError("Hosted provider endpoints require HTTPS.")
    if len(model) > 160 or not isinstance(model, str):
        raise ConfigurationError("Use a model identifier under 160 characters.")
    if re.search(r"AIza[\w-]{25,}|sk-(?:or-v1-)?[\w-]{25,}", model):
        raise ConfigurationError("Use a model identifier, not a credential value.")
    token_parameter = env.get(f"{prefix}_TOKEN_PARAMETER", profile.token_parameter)
    if token_parameter not in {"max_tokens", "max_completion_tokens"}:
        raise ConfigurationError("Choose max_tokens or max_completion_tokens for this profile.")
    return ProviderProfile(name, profile.adapter, base, profile.api_key_env, model, token_parameter, profile.require_key)


def credential(profile, environ=None):
    env = os.environ if environ is None else environ
    key = env.get(profile.api_key_env, "") if profile.api_key_env else ""
    if profile.name == "gemini":
        key = key or env.get("GOOGLE_API_KEY", "")
    return key


def configured(profile, environ=None):
    env = os.environ if environ is None else environ
    if profile.name == "vllm" and not env.get("VLLM_BASE_URL"):
        return False
    return bool(profile.model and (not profile.require_key or credential(profile, env)))


def public_status(environ=None):
    env = os.environ if environ is None else environ
    try:
        profile = resolve_profile(environ=env)
        return {**profile.public(), "configured": configured(profile, env),
                "fallback_provider": env.get("LLM_FALLBACK_PROVIDER", ""),
                "openrouter_free_only": env.get("OPENROUTER_FREE_ONLY", "true").lower() != "false"}
    except ConfigurationError as error:
        return {"provider": provider_name(env), "configured": False, "error": str(error)}
