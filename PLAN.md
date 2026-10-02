# AVP Tutor implementation plan

## Problem
Students need explanations of the algorithm and step they are watching. The upstream app generates code from function examples; it lacks execution context, conversation continuity, and learning-oriented evaluation.

## Orientation
Domains: learning design (hints and misconceptions), language/runtime correctness (AVP and execution snapshots), application engineering (API and accessible UI), operations (local Ollama and optional hosted providers), evaluation (held-out scenarios and reviewed training data).

## Proposed solution
A grounded tutor API accepts code, execution snapshots, recent events, and bounded conversation history. A temporary testing workspace (not the team's presentation frontend) demonstrates insertion sort using deterministic recorded steps. Students can request explanations, hints, or prediction questions. Versioned teaching notes provide explicit references. Retain upstream generation/retrieval endpoints for compatibility, with syntax validation for generated code.

## Assumptions and bets
The production visualizer can provide snapshots; this fork supplies an adapter contract and reference demo, not an implementation of the external interpreter. Local models need testing on real questions. Teaching quality comes from accurate context and curated examples; fine-tuning follows measurement. The user's priority is a useful tutor, not merely code generation.

## Alternatives
Raw-code fine-tuning is deferred because it lacks tutoring targets. Mandatory embedding downloads are replaced by lightweight lexical retrieval by default; semantic retrieval remains optional. Automated answer scoring is limited to smoke checks; human review remains necessary for educational quality.

## Deliverables and boundaries
Provider adapters; strict context schemas; sourced teaching notes; tutor endpoint; visual demo and chat; AVP syntax diagnostics; evaluated training-data export with grouped splits; tests; integration and deployment documentation. No model training is claimed without reviewed data and hardware decisions. Original history and attribution remain intact.

## Perspectives and dependencies
Artifacts serve students and integrating developers. AVP semantic claims require interpreter conformance verification. This is evolution of an existing project; upstream deployment destinations must not be reused. APIs are checked against documentation. No other team repository is modified.

## Delivery and verification
Write behavior tests before implementation. Verify backend, training export, TypeScript, frontend build, browser flows, and a live local-model request. Commit and publish to the user's confirmed fork after self-review; CI verifies the published revision. Future work: real visualizer integration, expert-reviewed datasets, controlled local-model fine-tuning.

## Delivery status
Implemented the backend, typed integration contract, editable skills, opt-in feedback, experimental candidate proposals, and dataset/evaluation tooling. Independent review identified shared inference limits and harness-version consistency issues; both have regression coverage and are fixed. Local checks and GitHub CI pass. The production frontend/interpreter adapter and instructor-reviewed training remain team integration work.

## Expanded development roadmap
The current authoritative roadmap is [docs/planning/WATERFALL.md](docs/planning/WATERFALL.md). The implementation plan above describes the delivered foundation. User additions belong in [docs/planning/NOTES.md](docs/planning/NOTES.md), with accepted changes recorded separately.
