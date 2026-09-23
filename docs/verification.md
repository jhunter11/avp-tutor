# Verification notes

Local checks on 2026-09-22/23:

- All 12 original `data/*.avp` programs pass syntax validation against the bundled parser. This does not verify execution semantics. The original language references are `Pseudocode.g4` and `PseudocodeSyntax.md`.
- Backend behavior tests cover strict schemas, API compatibility, context phase/values, invalid AVP diagnostics, provider routing/fallback, payload limits, rate limits, cache case sensitivity, training approval and grouped splits, prompt parity, and OpenAPI drift.
- Browser/client checks cover actual request context/history, references, readable errors, retry/cancel behavior, mobile overflow, framework-independent client behavior, and real-backend snapshot/trace integration.
- TypeScript and the production frontend build are checked. The frontend is an integration harness only.
- Dataset files validate. Default SFT export excludes all 19 drafts. Draft-preview export reports that its two independent algorithm groups are insufficient for a three-way split.

## Local-model observations

Tested with local Ollama `qwen3:8b`, 8.2B parameters, Q4_K_M quantization (local model digest prefix `500a1f067a9f`), thinking disabled, temperature 0.2, context 16,384, output limit 700. These are development observations from three insertion-sort cases, not a benchmark accuracy claim.

With final prompt `avp-tutor-v4`, the saved-key case correctly identified 3 being overwritten at index 1 by 8 while key retained 3. The hint case returned a short guiding question. The follow-up distinguished a copy/shift from a swap and named the correct values, but still added an unrequested stability explanation. Latencies were approximately 15.7s, 7.6s, and 14.5s on this machine. Earlier prompt versions produced an overly revealing hint and confused source/destination values, motivating explicit event details and stronger mode instructions.

This shows the integration works with a real local model and also identifies remaining teaching-quality work. Prompt instructions are not a correctness guarantee. Compare models and review the full development dataset before presentation; create an independent final test set before claiming measured improvements from fine-tuning. Hosted provider adapters have mocked SDK coverage. A live Gemini 3.5 Flash-Lite request also correctly explained the saved-key case; results are development observations, not measured accuracy. Gemini 3.8 Flash returned HTTP 503 and 2.5 Flash-Lite was unavailable to this account. No model was fine-tuned.

## Deployment limits

The local Docker daemon was unavailable, so container build/startup verification is included as a separate GitHub CI job. The optional BGE/FAISS stack is preserved but was not downloaded or exercised. The real team's AVP interpreter/frontend is outside this fork; its adapter and interpreter conformance tests remain integration work.
