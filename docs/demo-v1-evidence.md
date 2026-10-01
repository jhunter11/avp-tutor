# V1 verification record

Date: October 1, 2026. Actor: Codex. Environment: Windows, Python 3.14, and the Codex browser.

## Baseline and automated checks

The V1 branch starts from `3726490`, the existing teaching-workflow revision.
Before V1 changes, all 93 backend tests and Ruff checks passed.

After the core V1 changes, `uv run pytest -q` exited 0 with 111 passing tests.
`uv run ruff check .` exited 0.
`node --check demo_v1/web/app.js` exited 0.

The new checks cover exact code execution, immutable snapshots, loop limits, unsupported calls, bounds, and strict integer inputs.
They also cover question-to-confusion mappings, vector retrieval, optional memory, note deletion, credential-pattern rejection, and local request boundaries.
One randomized check compares 120 generated inputs against an independent first-match oracle.

## Observed browser behavior

The document loads on local port 8771.
The flawed draft returns `-1` for `[4, 7, 2, 7]` with target `7`, while the exercise expects index `1`.
The trace shows a return at line 7 with `i = 0`.
The fixed test count is four passes out of six.

Loading and running the corrected draft changes the custom output to `1` and the fixed count to six passes.
The trace shows the matching return at line 5 with `i = 1`.
These are observations from the actual bounded runner, separate from model output.

Previous-step controls change the recorded line and condition result.
An infinite loop reaches the execution limit and reports a readable error.
At a 390-pixel mobile viewport, the document has no horizontal overflow.
The temporary viewport override was reset after the check.

## Combined startup and provider verification

The canonical checkout includes the coordinated provider/startup commit and the container configuration fix.
Its combined backend suite exited 0 with 134 passing tests. Ruff and JavaScript syntax checks also exited 0.

`python demo.py doctor --json` confirmed the Windows prerequisites and the configured OpenRouter profile.
`python demo.py up --port 8771 --json` started the owned server and verified its root document.
A later call reused that same server with the same runtime fingerprint.
The selected model is `stealth/space-bunny-alpha`. Fallback is empty, and the free-only guard is enabled.
No credential value appears in the startup output.

The final canonical browser submitted a hint question with Enter and cleared the question field.
The live response took 6.5 seconds and named line 7, return `-1`, and index `0`.
It asked which later indices the program never checks. It did not print a corrected program.

The attached context identifies Your input, code hash prefix `c5033943c4b9`, and harness fingerprint `580a760c9b57`.
The displayed references include the linear-search notes, MathDial probing card, and OATutor graduated-hint card.
Up recalled the submitted question. Down restored the empty draft.

Two earlier browser requests in the combined worktree also returned useful answers.
The hint took 4.0 seconds. A debugging follow-up took 5.9 seconds.
The follow-up identified the premature return, explained index progress, and suggested matching and absent-input checks.
An older running process omitted the new attached-case field. Restarting the final runtime resolved that mismatch.

These are selected development observations. They are not an instructor-reviewed benchmark or a learning-impact score.
Gemini remains a selectable provider. This session did not test live Gemini inference.

## Teaching configuration follow-up

The final teaching follow-up has 150 passing backend tests.
Ruff and JavaScript syntax checks exited 0.
Sixteen new language and context regressions cover realistic questions and contract exclusions.
The pack now contains eight confusion cards, including zero-based indexing.
The runner records actual condition array reads and the loop depth of each return.

The selected live review covers nine scenarios and all four help styles.
The initial prediction request returned HTTP 503. One retry returned a useful prediction question.
The first missing-description response revealed a contract-reference leak, which the follow-up fixes.
A later answer reached the 700-token limit and returned only a fragment with a truncation warning.
The ignored local configuration now has a 1,600-token budget.
The final short-answer recheck reported the observed return and asked about intended output, with no warning.

See [the dated configuration review](teaching-config-review-2026-10-01.md) for individual answers and evidence limits.

## Evidence limits

The new runner supports a small AVP subset. It does not prove conformance with the production interpreter.
The method cards are draft coding adaptations. They have no instructor-reviewed quality or learning-impact scores.
V1 remains a separate document. The production visualizer adapter remains future work.
The coordinated publication workstream owns GitHub CI and the final pull request.
