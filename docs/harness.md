# Skills, context engineering, and a feedback-driven harness

The harness is the code around the model: choosing instructions, assembling execution context, retrieving teaching notes, controlling provider calls, and measuring outcomes. This repository makes those pieces inspectable and independently editable.

## Extension points

| Experiment | Files |
|---|---|
| Teaching skills | `harness/skills/*.md` |
| Number of retrieved notes / prior-question use / skill selection | `harness/configs/baseline.json` |
| Retrieval scoring, filtering, provenance | `tutor/knowledge.py`, `knowledge/*.md` |
| Snapshot schema and prompt assembly | `tutor/models.py`, `tutor/service.py` |
| Provider / model | `.env`, `providers.py` |
| Dataset / evaluation | `training/`, `docs/training.md` |

The server loads only a server-configured harness path, never a client-supplied file. Skill names must resolve within `harness/skills`. Response metadata includes the prompt, knowledge, and harness versions plus selected skill. A changed skill/config produces a new harness fingerprint. Freeze these artifacts for each experiment.

## Inspect context without spending API tokens

```sh
uv run python -m harness.inspect integrations/example-request.json > artifacts/prompt.json
uv run python -m harness.inspect integrations/example-request.json --harness artifacts/candidate/harness.json
```

The report shows exact model messages, selected skill, reference IDs, prompt character count, and version fingerprints. This makes retrieval/context changes inspectable before evaluation.

## Learning signals

Explicit answer feedback: helpful, incorrect, too much answer, too vague, or missing context, with an optional explanation. These are reports, not verified correctness labels. Store them alongside the actual request, returned answer, model, and harness versions so a reviewer can reproduce the problem.

Usage signals: offered, opened, dismissed, asked, and prediction-correct/incorrect. These are recorded separately, without a learner/session identifier or free-text payload. Non-use is **not negative feedback**: it can indicate understanding, distraction, invisibility, or friction. Prediction events are frontend-reported observations, not independently verified outcomes. The initial implementation supports aggregate counts, not causal attribution or student-level learning estimates.

For future learning-impact experiments, predefine consented pseudonymous session/event linkage, exposure windows, and outcome measures with your team. Randomized harness variants and delayed transfer questions are stronger evidence than clicks or thumbs-up alone. Avoid optimizing for more AI usage; a helpful tutor may reduce dependence on it.

## Opt-in capture and deletion

Set `FEEDBACK_ENABLED=true` on a local/research server. The frontend must explain that questions, code/state, conversation, and answers will be saved for review, then send `feedback_consent=true` on the particular `/api/tutor` request. Without both switches, nothing is captured. Failed model calls are not captured. The response returns an opaque `interaction_id` when saved.

```json
POST /api/feedback
{"interaction_id":"opaque-id-from-response","rating":"too_much_answer","comment":"I wanted a clue, not the answer."}
```

One current vote is stored per interaction; resubmission updates it instead of amplifying the vote. `DELETE /api/feedback/{interaction_id}` removes the saved request, answer, and feedback. The opaque ID is a capability: keep it with the owning student's interaction, do not publish it. Public deployment still requires the team's authenticated gateway and ownership controls. No endpoint lists stored conversations.

```json
POST /api/usage
{"consent":true,"event":"dismissed","algorithm":"insertion_sort"}
```

Storage is local SQLite, default `artifacts/feedback.sqlite3` (gitignored), file mode 0600. Records older than 30 days are purged when the store opens; there is no background retention job. Deploy a scheduled purge if strict time-based deletion is required. Usage is aggregate and unlinked; do not include personal identifiers in algorithm names. Disable capture outside consented experiments.

## Self-scaffolding loop

The current implementation creates **candidate configurations**, not autonomous production edits:

```sh
uv run python -m harness.improve --db artifacts/feedback.sqlite3 --output artifacts/candidate
uv run python -m training.evaluate --limit 10 --output artifacts/baseline.jsonl
uv run python -m training.evaluate --harness artifacts/candidate/harness.json --limit 10 --output artifacts/candidate.jsonl
```

Three or more “too much answer” reports propose a more constrained hint skill. Repeated missing-context reports propose testing one extra teaching note, explicitly warning that extra retrieval cannot restore missing runtime state. Incorrect-answer reports request review against interpreter evidence. These simple thresholds are experimental scaffolding, not statistically justified promotion rules.

The proposal records feedback counts and intended checks; it never rewrites the active config, changes model weights, marks examples approved, or installs generated code. No user comment is executed as an instruction. An instructor reviews baseline/candidate answers for state accuracy, algorithm correctness, teaching usefulness, latency, and regressions. Promote a reviewed candidate explicitly through version control and `HARNESS_CONFIG`. Re-run the same evaluation after promotion and retain the prior config for rollback.

A future model-driven proposer can draft skill changes or retrieval policies in an isolated candidate directory. Keep the same replay, provenance, and review boundary. Prefer adapting the harness first; collect reviewed corrections for SFT only after identifying failures that context/skills do not resolve.
