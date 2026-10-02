# Teaching configuration review

Date: October 1, 2026. Actor: Codex. Runtime: Windows and the standalone V1 document.

The selected question asks for the first zero-based matching index, or minus one when no match exists.
This review checks a fixed teaching pack for that question.
It is development evidence, not an instructor review or a student-learning study.

## Configuration under review

| Component | Bound |
|---|---|
| Teaching skills | Four fixed files: Hint, Explain, Debug, Predict |
| Confusion cards | Eight project-authored hypotheses |
| Coding retrieval | At most three lexical fact sections |
| Method retrieval | At most two cards from three local TF-IDF vectors |
| Model | OpenRouter, `stealth/space-bunny-alpha` |
| Fallback | None |
| Price guard | Zero-price catalog check and routing limits |
| Learner notes | Off during this review |
| Execution | Actual edited AVP in the bounded demo interpreter |

MathDial and OATutor inform the draft method cards.
The cards retain source links, revisions, and license labels in `demo_v1/pedagogy.json`.
Their coding adaptations need instructor review.
Term vectors retrieve a relevant method. They do not train a model or prove transfer from mathematics to coding.

## Problems found and changes

Generic words produced poor initial choices.
For example, a question about returning minus one despite an existing target selected the absence card.
The revised selector uses actual array reads and return scope when it assesses a result question.
It keeps generic matches as hypotheses when execution does not support a specific cause.

The pack lacked guidance for counting the first position as one.
It now includes a zero-based-indexing card and a fact section that labels indices and stored values.
Word boundaries prevent the word `value` from matching the identifier `values`.
Definition questions about length receive the length section without a misconception label.

A negative control showed that excluding the last index could resemble a premature return.
The selector now requires a return inside a loop before choosing that cause from execution evidence.
The runner records actual condition reads, including computed indices and Boolean short-circuit behavior.
These rules cover this bounded exercise. They do not perform complete semantic analysis.

The first live test without a problem description still retrieved the exercise contract.
The model then asserted an expected first-match output.
The revised context excludes contract references, expected results, and pass labels in that mode.
It also removes specification-dependent confusion cards, even when the question contains no result-related keyword.
Result questions now request the learner's intended output before a semantic correction.

## Selected live observations

The table shows final useful observations for nine selected scenarios.
Each response used the configured OpenRouter model.
Codex compared the answers with the supplied code, trace, and requested help style.

| Scenario | Help style | Observed response | Seconds |
|---|---|---|---|
| Existing target, actual minus one | Hint | Asked which indices the return had checked | 5.579 |
| Returns value 7, expects index 1 | Debug | Identified `return values[i]` and suggested `return i` | 6.273 |
| Counts the first position as one | Explain | Distinguished second position from index 1 | 6.318 |
| Repeated target returns the last match | Hint | Compared matching indices 0 and 2 | 3.625 |
| Missing target returns zero | Debug | Explained the ambiguous sentinel and suggested minus one | 7.902 |
| Defines `length(values)` | Explain | Counted three values and labeled valid indices | 4.444 |
| Predicts after the initial loop condition | Predict | Asked which two values the next comparison uses | 6.089 |
| No problem description | Debug | Reported the observed return and asked about intended output | 6.013 |
| Requests a different explanation of indexing | Explain | Used a small index/value diagram | 4.611 |

The first hint said: "When line 7 returns `-1`, which array indices has the function checked so far?"
It gave one clue and did not print a corrected program.

The final response without a description said:
"Line 7 returns `-1` after checking only `values[0] = 4`, so the `7` at index 1 is never checked."
It then asked, "What result did you intend your solution to return?"

## Failures and output budget

The initial prediction request returned HTTP 503. One retry returned the useful prediction question above.
The first response after the missing-description fix reached the 700-token output limit.
Its visible text was only `On [`, and the API returned a truncation warning.
This response was not useful.

The local demo now has a 1,600-token budget in its ignored `.env` file.
A short-answer recheck returned a complete clarification in 6.013 seconds with no warning.
That observation does not establish an optimal output budget or provider reliability.
The public provider default remains unchanged.

Changing the local output budget requires stopping and starting the owned demo:

```sh
python demo.py stop --json
python demo.py up --port 8771 --json
```

## Reproduce the deterministic checks

```sh
uv run pytest -q tests/test_demo_teaching_language.py tests/test_demo_teaching_matrix.py tests/test_demo_v1.py tests/test_demo_runtime.py
uv run pytest -q
uv run ruff check .
node --check demo_v1/web/app.js
```

The checks include realistic language, negative controls, all four skills, retrieval bounds, and 120 randomized inputs.
The randomized inputs compare execution with an independent first-match oracle.
They do not score the model's teaching quality.
The final full suite exited 0 with 150 passing tests and nine dependency deprecation warnings.
Ruff and JavaScript syntax checks also exited 0.

Local API receipts remain in the ignored `artifacts/teaching-review-20261001/` folder.
They contain questions, code, answers, timing, source IDs, and version hashes.
They contain no API key or session-token header.
The manifest distinguishes the earlier failures from the final useful observations.

The model remains variable across requests.
The runner covers a small AVP subset and needs production-interpreter conformance checks.
Teacher review, student reasoning checks, and transfer evaluation remain later project work.
