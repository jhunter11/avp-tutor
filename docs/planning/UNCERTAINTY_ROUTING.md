# Uncertainty-aware local-to-API routing experiment

CR-002 · Proposed research scope · 2026-09-23 · Not implemented in the live tutor

## User proposal

Monitor uncertainty during local inference. An unusual increase could trigger a stronger hosted model for a difficult explanation, or identify a recurring problem that the self-scaffolding harness should address. Preserve local-first operation while learning which failures warrant a different intervention.

## Hypotheses to test separately

H1: a measurable uncertainty signal predicts incorrect or pedagogically inappropriate AVP responses on unseen tasks.

H2: selecting an intervention using that signal improves correctness or teaching quality at an acceptable cost and latency compared with a fixed policy.

A positive H1 does not establish H2. Token entropy measures next-token uncertainty; many valid phrasings can raise it, and confidently incorrect answers can have low entropy. An unfamiliar explanation style may change token distributions without changing correctness. This measures model uncertainty, not student mastery or the entropy of unobserved latent reasoning.

## Capability and measurement

Current adapter sends `think=false` and `stream=false` to Ollama and does not collect probabilities. Existing provider fallback handles call failures only. It is not quality-triggered routing.

Current [Ollama chat documentation](https://docs.ollama.com/api/chat) lists `logprobs` and `top_logprobs`. Verify these on the installed server/model before implementation; request acceptance is not proof the fields are returned. Record server version, model digest, quantization, sampling settings and prompt/harness versions. If unavailable, compare an instrumented local backend against sampled-answer disagreement rather than inventing entropy values.

Local capability probe on 2026-09-23: Ollama 0.31.1 with `qwen3:8b`, `think=false`, `stream=false`, `logprobs=true`, `top_logprobs=5`, and an eight-token output cap returned HTTP 200 with nonempty `logprobs`. This confirms basic answer-token telemetry only; full-vocabulary entropy, streaming probability delivery and reasoning-token alignment remain unverified. No hosted API call was made for this probe.

For a full distribution, token entropy is H = -sum(p log p). Chosen-token surprise (-log p of the emitted token) is a different quantity. A top-k list alone is not full-vocabulary entropy: retain covered probability mass and label any top-k statistic or bound explicitly. Never silently renormalize the top-k list and call it full entropy. Document sampling transformations and whether probabilities are before/after temperature or truncation.

Begin with answer-level shadow monitoring. Streaming interruption is a later extension requiring confirmed streamed probability support, cancellation and resource cleanup. Do not assume emitted thinking text exposes internal reasoning states or that answer-token uncertainty measures reasoning-token uncertainty. Do not require raw internal reasoning to be stored or displayed to students.

## Signals to compare

- Interpreter/verifier conflicts: wrong value, wrong line/phase, unsupported execution claim.
- Context completeness and retrieval coverage: may call for missing information, not a larger model.
- Chosen-token surprise and, when available, distribution/top-k statistics; normalize against matched task/mode/model baselines.
- Meaning-level disagreement among independently sampled answers, with added sampling/semantic-check cost recorded.
- Output truncation, unsupported citations and repeated unresolved misconceptions.

[Semantic uncertainty research](https://arxiv.org/abs/2302.09664) motivates separating wording variation from disagreement about meaning; its question-answering results are not validation for AVP tutoring. Evaluate factual and pedagogical failure labels separately.

## Proposed routing policy

1. Validate the snapshot and find required facts; ask for clarification if essential state is missing.
2. Generate a local candidate and collect supported signals. In shadow mode, record the would-be route without changing the delivered response.
3. Apply a calibrated policy to choose: accept local answer, perform a bounded verifier check, retrieve a missing reference/retry locally, ask the student for missing context, or escalate to the configured API.
4. For authorized cloud routing, send the original question, authoritative snapshot, references and teaching objective. If including a local draft, label it untrusted; do not present it as established fact.
5. Check the hosted response too. A larger/API model is not ground truth. If both candidates fail or required evidence is missing, return a clear limitation rather than choosing the more confident answer.
6. Record route, reasons, available/missing signals, selected action, actual provider, outcome, total latency and cost. Cap retries and prevent recursive escalation.

Cloud routing remains off unless configured and permitted for that session's data. Distinguish ordinary provider-availability fallback from quality escalation in settings and telemetry. A declined or unavailable API path must still support a local clarification or conservative answer. Research collection remains opt-in and must not quietly expand existing consent.

## Evaluation design and acceptance gates

Use trace-grounded AVP cases with independent correct-answer labels plus instructor-reviewed pedagogy labels. Include advanced and simple tasks, confidently wrong examples, unfamiliar valid wording, new explanation styles, missing state, and multiple implementations. Keep final evaluation separate from detector/threshold tuning and shared prompt templates. Difficulty labels and signal thresholds must not be selected after viewing final results.

Compare local-only, always-API, random escalation at matched API rate, verifier-only routing, and uncertainty-based routing. Compare continue/verify/retrieve/clarify/escalate outcomes on the same frozen cases; use randomized action assignment where needed to identify intervention benefit. Match compute/cost budgets where possible and report quality-cost-latency curves where exact matching is impossible. A small smoke run cannot establish a routing advantage.

Report detector precision/recall and false-escalation rates, missed confident errors, calibration where probabilities are claimed, escalation frequency, factual/teaching quality, p50/p95 latency, tokens/cost and privacy-policy violations. Human review is blinded to provider/route where practical. Track whether extra API calls actually rescue failed answers and whether they introduce new errors.

Gate A: capability verified and metric semantics documented. Gate B: held-out predictive value beyond cheap verifiers and task difficulty. Gate C: intervention improves measured outcomes at a predeclared budget. Gate D: consent, failure handling, rollback and rate limits verified. Only then enable a reviewed policy beyond shadow mode. Numeric thresholds, sample-size rationale and success criteria remain to be specified before the study.

## Feedback to the self-scaffolding harness

Group verified failures by concept, context gap, retrieval coverage, explanation strategy and model version. A spike is a diagnostic observation, not a training label. Propose a skill/context/retrieval change when recurring evidence identifies a plausible cause; replay it against the fixed baseline and held-out cases. Do not optimize merely to lower entropy or reduce API calls: confident errors could make either metric look better.

Candidate objectives: preserve factual correctness and student learning while controlling latency/cost. Keep personalized learner adaptation separate from global router updates. Neither a cloud answer nor a low-entropy local answer is automatically a human-approved SFT target.

## Waterfall placement

Phase 1: define quality escalation, privacy and budget requirements. Phase 2: construct detector/intervention evaluation cases. Phase 3: capability/telemetry and routing design. Phase 4: implement shadow metrics and bounded interventions. Phase 5: replay tests and failure handling. Phase 6: calibrated comparison/pilot. Phase 7: reviewed rollout with rollback. Phase 8: optional use of reviewed corrections for training.

This is a research extension, not a dependency for the initial presentation release unless the user changes its priority. Presentation target supplied in notes: April 2027. Potential dedicated RTX 5090 and expansion to many algorithms remain planning possibilities, not acquired hardware or implemented coverage.
