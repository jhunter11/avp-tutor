# Tutor workflow improvement pass

Scope: implement a bounded improvement of the question-to-answer workflow requested by the user, preserving the team's frontend and user notes. This is not completion of all fifteen research ideas.

## Design

Separate execution evidence checking, example selection, and teaching decisions from provider calls. Inputs remain backward compatible: add an optional code version and explicit explanation strategy. A context SHA-256 and bounded same-algorithm code samples identify exactly what informed an answer. Samples are syntax checked but are never represented as executed/equivalent to the current program. A deterministic decision honors explicit mode/strategy; conflicting structured events lead to clarification guidance rather than unsupported inference. Lightweight response checks flag unknown citations  without claiming full answer verification.

## Tasks and verification

- [x] Write failing tests in `tests/test_workflow.py`: code hashes differ on edits; explicit strategy honored; unknown code never forces a match; examples are bounded and distinguished from current code; stale events not compared to a later snapshot; current structured copy conflicts detected; no claim of semantic verification; runtime/inspection/training share context assembly; unknown citations flagged.
- [x] Add `tutor/evidence.py`: hash exact input code, inspect only the latest event when its line/phase matches, and report scoped checks/conflicts/unverifiable cases. Do not infer array identity when ambiguous.
- [x] Add `tutor/examples.py`: read bounded repository AVP samples with per-file hashes and syntax validation, match normalized algorithm labels, exclude exact current code; no embedding download or external source import.
- [x] Add `tutor/teaching.py`: versioned strategy instructions and deterministic decision reasons; add fields in `tutor/models.py` and optional policy limits in `harness/config.py`.
- [x] Integrate one prepared workflow into prompt assembly, response metadata, inspection and export. Freeze the actual examples and instruction text used; expose a fingerprint of the exact assembled messages.
- [x] Extend the temporary frontend with strategy selection and expandable workflow evidence; regenerate OpenAPI/client declarations. Add browser coverage for request/response behavior.
- [x] Run Ruff, full pytest, TypeScript build and browser tests; inspect one offline request and a bounded live local model request; update meeting guide and integration docs. Commit only authored files, publish a PR and inspect CI. Leave `docs/planning/NOTES.md` unchanged.

Acceptance: backward-compatible existing tests; added negative-path tests; no silent cloud usage; no persistent learner-profile or independent execution claims; failure diagnostics contain no provider credentials. Public datasets remain research-only.

Validation: 93 backend tests and Ruff passed; production frontend build passed. Browser strategy coverage and local inference are verified separately in the delivery record. Checks do not establish factual answer accuracy.
