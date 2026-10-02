# A runnable tutoring workflow

The tutor takes the student's exact code and paused execution snapshot, retrieves teaching notes and bounded reference implementations, chooses a teaching approach, and asks the configured model to respond. These are backend features; the temporary frontend is a testing tool.

1. Capture the question, mode, level, optional strategy, recent conversation, and interpreter snapshot together. `context.code_version` can identify the frontend's revision; the backend hashes the exact code itself.
2. Check supplied evidence. Current-line after-phase copy/shift events can be compared with the array and saved key. Conflicts select a clarification action. Matching fields do not prove correct execution: the interpreter must supply a synchronized event and snapshot.
3. Retrieve relevant teaching notes and at most one full AVP example by default (configurable up to two; 6,000 characters total). Examples match the algorithm label, pass syntax validation, and carry hashes. They are not proven equivalent to the student's program. Unknown algorithm labels produce no forced example match.
4. Choose trace, analogy, comparison, invariant, worked example, or guided question. An explicit preference is honored subject to question mode and evidence constraints. This is a transparent policy, not an inferred permanent learning style.
5. Assemble one prompt with separated evidence, reference code, notes, and teaching instructions. Hash the messages actually sent. Runtime, offline inspection, and training export share assembly.
6. Call the configured provider. This pass does not introduce automatic cloud escalation.
7. Return the answer, decision and reasons, evidence report, reference examples, prompt hash, and warnings. Unknown citation identifiers are flagged; factual accuracy is not independently verified.
8. Existing opt-in feedback can inform reviewed harness candidates. A dismissed answer is not proof of failure, and no automatic model training or live harness promotion occurs.

## Inspect without paying for inference

From the repository root, create a reproducible request:

```sh
uv run python - <<'PY'
import json
from pathlib import Path
from tutor.demo import build_trace
frame = next(f for f in build_trace([2, 7, 9, 4]) if f.recent_events[-1].kind == 'shift')
Path('/tmp/avp-workflow.json').write_text(json.dumps({
    'question': 'Did we lose the 4?', 'mode': 'explain',
    'strategy': 'analogy', 'context': frame.model_dump()
}))
PY
uv run python -m harness.inspect /tmp/avp-workflow.json
```

With your configured backend running, send the same request:

```sh
curl --fail-with-body http://localhost:8000/api/tutor \
  -H 'Content-Type: application/json' --data-binary @/tmp/avp-workflow.json
```

Change `strategy` to `trace` or `guided-question` to compare responses with the same evidence. Corrupt a copied array value to demonstrate the clarification decision. Inspect `evidence`, `teaching_decision`, `code_examples`, and `prompt_sha256` in the response.

For the meeting: “We give the tutor the exact paused program, useful reference code, and what the student asked. It chooses a teaching approach, tells us why, and identifies contradictory context before trying to explain it. We can compare approaches without changing the model.”

Next experiments remain separate: independent interpreter verification, measured learning outcomes, learner-state estimates, and uncertainty-based API routing. The current checks are not evidence those experiments work.
