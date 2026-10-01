# V1 verification record

Date: October 1, 2026. Actor: Codex. Environment: Windows, Python 3.14, and the Codex browser.

## Baseline and automated checks

The V1 branch starts from `3726490`, the existing teaching-workflow revision.
Before V1 changes, all 93 backend tests and Ruff checks passed.

After V1 changes, `uv run pytest -q` exited 0 with 111 passing tests.
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

## Provider verification checkpoint

Live OpenRouter verification belongs to the coordinated provider/startup workstream.
This checkpoint does not claim a completed live answer or a current Gemini result.
The demo's mocked answer test confirms provider-neutral metadata and the selected fixed skill.

## Evidence limits

The new runner supports a small AVP subset. It does not prove conformance with the production interpreter.
The method cards are draft coding adaptations. They have no instructor-reviewed quality or learning-impact scores.
The existing frontend and production services have no changes in this V1 commit.
Later provider and startup commits require combined verification.
