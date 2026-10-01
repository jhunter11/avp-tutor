# Text-chat provider configuration

The demo and integration API share the same provider layer.
Select a profile with `LLM_PROVIDER` or `demo.py --provider`.
Select an exact model with the profile's model variable or `--model`.

| Profile | Credential variable | Model variable | Adapter |
|---|---|---|---|
| openrouter | OPENROUTER_API_KEY | OPENROUTER_MODEL | OpenRouter chat |
| gemini | GEMINI_API_KEY or GOOGLE_API_KEY | GEMINI_MODEL | Google OpenAI-compatible chat |
| openai | OPENAI_API_KEY | OPENAI_MODEL | OpenAI-compatible chat |
| anthropic | ANTHROPIC_API_KEY | ANTHROPIC_MODEL | Anthropic messages |
| ollama | none | OLLAMA_MODEL | Ollama chat |
| vllm | VLLM_API_KEY, optional | VLLM_MODEL | OpenAI-compatible chat |
| compatible | COMPATIBLE_API_KEY, optional | COMPATIBLE_MODEL | OpenAI-compatible chat |

OpenRouter defaults to `stealth/space-bunny-alpha`. Availability and limits can change.
Before a completion, the default free-only policy checks the live catalog for zero prices.
It also sends zero price caps and disables provider fallback within OpenRouter.
Unknown pricing, catalog failure, and paid models stop the request.
`OPENROUTER_FREE_ONLY=false` explicitly permits priced models. It does not change account limits.
See [OpenRouter routing controls](https://openrouter.ai/docs/guides/routing/provider-selection).

Gemini uses [Google's documented compatibility endpoint](https://ai.google.dev/gemini-api/docs/openai).
Set a Gemini key and a model available to that key when ready.
The Gemini adapter never uses an OpenRouter key.
Named Gemini and OpenRouter profiles require HTTPS and keep their service credential variables and hosts.

Example local configuration:

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GEMINI_MODEL=your-available-model-id
```

The API key line above is blank. Enter the real value through a local terminal prompt or secret manager.
Restart after configuration changes. Credentials remain on the server.
Cross-provider fallback is off unless `LLM_FALLBACK_PROVIDER` names another configured provider.
An explicit fallback can send the same learner context to that provider.

## Add another compatible provider

Add a public profile to config/providers.json, or select a separate file with `LLM_PROVIDERS_FILE`.
Each profile has these fields:

```json
{
  "adapter": "openai-compatible",
  "base_url": "https://example.org/v1",
  "api_key_env": "MY_PROVIDER_API_KEY",
  "model": "available-model-id",
  "token_parameter": "max_tokens",
  "require_key": true
}
```

Use `max_completion_tokens` if that service requires it.
Profiles contain credential variable names, never credential values.
Per-profile MODEL, BASE_URL, and TOKEN_PARAMETER environment variables override public defaults.
For example, a `my_provider` profile uses `MY_PROVIDER_MODEL`.
Named Gemini and OpenRouter ignore BASE_URL overrides to retain their documented service hosts.

These adapters support text chat. They do not promise every vendor-specific API, multimodal feature, or tool protocol.
A provider with a different wire protocol needs an adapter.

## Verify

Run `doctor --json` for configuration checks and `verify-model --json` for one live synthetic request.
Unit tests cover Gemini routing, provider extensions, missing keys, and free-only routing.
The development machine verified live OpenRouter inference.
Gemini has configuration tests but no live check because no Gemini key is configured.

## Output limits

`LLM_MAX_TOKENS` controls the requested output budget. The default remains 700, with a maximum of 4096.
The page shows a warning when the provider reports a truncated answer.
For a larger budget, set `LLM_MAX_TOKENS=1600` in the local environment file and restart.
Selected demo rechecks completed at that setting after an earlier truncated response.
Those observations do not establish a reliability rate or prove that the budget change caused the improvement.
Provider failures can still occur. Keep the failure and truncation warnings visible during a demo.
