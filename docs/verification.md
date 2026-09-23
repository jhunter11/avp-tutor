# Verification notes

Local checks on 2026-09-22/23:

- All 12 original `data/*.avp` programs pass syntax validation against the bundled parser. This does not verify execution semantics. The original language references are `Pseudocode.g4` and `PseudocodeSyntax.md`.
- 79 backend tests and 15 browser/client tests pass locally; TypeScript and production build pass.
- Backend behavior tests cover strict schemas, API compatibility, context phase/values, invalid AVP diagnostics, provider routing/fallback, payload limits, rate limits, cache case sensitivity, training approval and grouped splits, prompt parity, and OpenAPI drift.
- Browser/client checks cover actual request context/history, references, readable errors, retry/cancel behavior, mobile overflow, framework-independent client behavior, and real-backend snapshot/trace integration.
- TypeScript and the production frontend build are checked. The frontend is an integration harness only.
- Dataset files validate. Default SFT export excludes all 19 drafts. Draft-preview export reports that its two independent algorithm groups are insufficient for a three-way split.

## Local-model observations

Tested with local Ollama `qwen3:8b`, 8.2B parameters, Q4_K_M quantization (local model digest prefix `500a1f067a9f`), thinking disabled, temperature 0.2, context 16,384, output limit 700. These are development observations from three insertion-sort cases, not a benchmark accuracy claim.

With final prompt `avp-tutor-v4`, the saved-key case correctly identified 3 being overwritten at index 1 by 8 while key retained 3. The hint case returned a short guiding question. The follow-up distinguished a copy/shift from a swap and named the correct values, but still added an unrequested stability explanation. Latencies were approximately 15.7s, 7.6s, and 14.5s on this machine. Earlier prompt versions produced an overly revealing hint and confused source/destination values, motivating explicit event details and stronger mode instructions.

This shows the integration works with a real local model and also identifies remaining teaching-quality work. Prompt instructions are not a correctness guarantee. Compare models and review the full development dataset before presentation; create an independent final test set before claiming measured improvements from fine-tuning. Hosted provider adapters have mocked SDK coverage. A live Gemini 3.5 Flash-Lite request also correctly explained the saved-key case; results are development observations, not measured accuracy. Gemini 3.8 Flash returned HTTP 503 and 2.5 Flash-Lite was unavailable to this account. No model was fine-tuned.

## Deployment limits

The local Docker daemon was unavailable. GitHub CI successfully built and started the container, and passed backend/dataset and frontend/browser checks (run 35875315870). The optional BGE/FAISS stack is preserved but was not downloaded or exercised. The real team's AVP interpreter/frontend is outside this fork; its adapter and interpreter conformance tests remain integration work.

## Gemini development smoke run

On 2026-09-23, `gemini-3.5-flash-lite` was tested through Google's OpenAI-compatible endpoint using the same harness on five selected development cases, with a 2,048-token output cap and no fallback. Four returned answers: saved-key preservation, shift-versus-swap follow-up, binary-search sorted-input requirement, and parsing-versus-execution. Inspection found those expected facts present; the hint request failed at the provider boundary after waiting. These four responses are not a quality percentage or an instructor-reviewed benchmark. The run emitted no unknown-citation flags on successful answers. Local reports are ignored by Git, and no credentials were copied or published.

Reproduce using the existing local key file:

```sh
LLM_PROVIDER=gemini GEMINI_MODEL=gemini-3.5-flash-lite LLM_MAX_TOKENS=2048 uv run python -m training.evaluate --env-file /absolute/path/to/avp-project/.env --limit 5 --output artifacts/gemini.jsonl
```

This command uses the first five development cases; the observed run selected cases 0, 1, 2, 40, and 49 to cover more topics. Model availability and latency can change. Human rubric fields remain unfilled; no model was trained.
