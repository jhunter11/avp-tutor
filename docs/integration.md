# Visualizer integration

The tutor consumes **observations from your interpreter**. It does not execute arbitrary submitted AVP, control the production visualizer, or infer authoritative state from screenshots.

## Frontend handoff

Use the [standalone typed client](../integrations/README.md) or call the REST API directly from your team's UI. The bundled frontend is only an integration/testing harness. Generated types and an OpenAPI snapshot are committed, with drift tests to keep them aligned with the backend.

## Request

```json
{
  "question": "Did we lose the 4?",
  "mode": "explain",
  "level": "beginner",
  "history": [],
  "context": {
    "algorithm": "insertion_sort",
    "language_version": "avp-repository-v1",
    "code": "collection[j + 1] = collection[j]",
    "current_line": 1,
    "phase": "after",
    "run_id": "run-42",
    "step": 7,
    "variables": {"j": 2, "key": 4},
    "arrays": {"collection": [2, 7, 9, 9]},
    "recent_events": [{
      "kind": "shift",
      "description": "Copied 9 from index 2 to index 3; key still holds 4.",
      "line": 1,
      "indices": [2, 3]
    }]
  }
}
```

`current_line` is **one-based within the submitted code**. If sending a snippet, remap line numbers to the snippet. `phase=after` means the highlighted statement has already executed. If your visualizer highlights the next instruction, use `before`. A snapshot is captured atomically at question submission. Include concrete events from the actual interpreter and explicit code/runtime version.

Modes: `explain`, `hint`, `predict` (asks the student a prediction question), `debug`. Levels: `beginner`, `intermediate`, `advanced`. Neither a system role nor arbitrary options/URLs/API keys are accepted from the frontend.

History contains only `user` and `assistant` content. Submit the most recent relevant completed turns; old state is not authoritative. Reset history on changing algorithms/runs. The demo annotates old turns with step numbers and pauses playback while asking. For questions about earlier runs, send that run's snapshot explicitly.

## Limits and responses

Requests are limited to 128 KiB before JSON parsing. Questions are nonempty and at most 4,000 characters; code at most 16,000; context at most 24,000 serialized characters; history at most 12 messages / 12,000 characters; each visible array at most 256 values; events at most eight. Trim upstream context deliberately instead of silently dropping state. Unknown schema fields produce 422.

The response includes `answer`, `sources`, `warnings`, `context_status`, actual `provider`/`model`, latency, optional usage, prompt/knowledge versions, and fallback status. `sources` means notes **provided to the model**, not proof every claim used them. `provided` context means required observation fields were supplied, not independently verified execution. There is deliberately no model-invented confidence score. Tutor answers are not globally cached. They are logged only when both server feedback capture and per-request consent are enabled; see [feedback integration](harness.md).

Handle 422 (invalid request), 429 (rate limited), and 503 (provider unavailable/busy). Preserve the question so students can retry. Canceling in the browser stops waiting; an in-flight server/model call may continue until its configured timeout. Two model calls per process may run concurrently. Multi-worker deployments multiply that limit and use per-process rate limiting; use a shared gateway/limiter when scaling.

## AVP conformance

The bundled grammar differs from the written reference in whitespace handling and nested functions. `/api/validate` reports grammar syntax success separately from documented semantic/style diagnostics and always returns `execution_verified=false`. It is not a complete scope/type/bounds checker. Run interpreter conformance tests before declaring this parser compatible with a production AVP runtime.

The insertion-sort demo is a deterministic Python reference trace whose displayed AVP has the same algorithm structure. It is not a general AVP interpreter and does not implement visualization annotations. Replace its snapshots with your actual interpreter events at the integration boundary.
