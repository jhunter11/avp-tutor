# AVP Tutor — Waterfall development plan

Version 1.1 · 2026-09-23 · Working baseline, open to user amendments

This plan distinguishes delivered software from proposed development. Phase order is deliberate: establish evidence and requirements before building learner models, then validate learning outcomes before adaptive policy promotion or fine-tuning. Phase gates are project milestones, not requests for permission to complete work already authorized.

## 1. Purpose and scope

Build an algorithm tutor integrated into the team's visualizer that explains the actual execution state, offers multiple teaching approaches, and adapts from evidence about understanding. Students should be able to ask questions, request another explanation, make predictions, receive graduated hints, and inspect or reset their learning profile.

The backend, context adapter contract, teaching skills, retrieval, evaluation, and learner adaptation are in scope. The team's frontend remains the product UI; this repository's frontend is a temporary test harness. The external AVP interpreter remains authoritative for runtime behavior. Public mathematical tutoring data supports pedagogy, not AVP syntax or execution claims.

Domains: learning science, language/runtime correctness, backend integration, product UX/accessibility, research evaluation, data governance, deployment. Required expertise: interpreter maintainer, frontend developer, backend developer, instructor/reviewer, and experiment owner. These are proposed roles; named owners and dates remain unassigned.

Assumptions to validate: interpreter snapshots are available; students can provide optional feedback; enough distinct tasks exist for transfer checks; local inference latency is acceptable; observed response preferences are not necessarily evidence of better learning. A risk is becoming attached to personalization before showing that it improves understanding. A clear fixed tutor remains the comparison baseline.

## 2. Current state and evidence

Baseline application commit: `9cd6a75`. Dataset acquisition and this plan are additions to that baseline.

| Capability | Status | Evidence / limitation |
|---|---|---|
| Tutor API: explain, hint, predict, debug | Implemented | Strict request and snapshot schemas; bounded history and model concurrency |
| Ollama and Gemini routing | Implemented, smoke tested | Local Qwen3 tested; Gemini 3.5 Flash-Lite returned four answers in a five-case development run, with one failure |
| Execution grounding | Implemented for supplied context | Reference insertion-sort demo; real interpreter adapter not implemented |
| AVP validation | Implemented | Grammar, syntax reference, 12 sample programs; parsing is not execution verification |
| RAG | Implemented | Small lexical teaching-note collection; optional legacy semantic stack unverified |
| Versioned teaching skills | Implemented | Four modes, experimental constrained hint skill, config/prompt/knowledge fingerprints |
| Feedback | Implemented, opt-in | Saved interactions and one current rating per interaction; aggregate usage recorded separately |
| Candidate harness proposer | Implemented prototype | Heuristic proposals; no automatic live changes, learning guarantee, or weight updates |
| Training/evaluation | Implemented foundation | 19 draft targets, 50 development cases, approval-gated export, grouped splits |
| Product frontend | External/team-owned | Typed client and OpenAPI contract supplied; no product integration yet |
| Public teaching sources | Added research collection | See `datasets/README.md` for exact downloaded scope and access gaps |
| Learner profiles | Planned | No persistent per-student mastery or strategy-effect model |
| Verified understanding checks | Planned | Current usage events are frontend reports, not verified assessment results |
| Personalized strategy policy | Planned | Current skills are mode-based; no learned per-user strategy selection |
| Model post-training | Not started | No approved AVP training corpus or trained adapter |

Prior verification: 79 backend tests and 15 local browser/client tests; GitHub CI run 35875709427 passed backend, frontend, and container startup checks. Those counts describe the application baseline; new dataset-tool tests have their own verification. Smoke responses are not benchmark accuracy or evidence of learning gains.

## 3. Requirements baseline and traceability

| ID | Requirement | Planned artifact | Acceptance evidence |
|---|---|---|---|
| R01 | Explain the real execution step | Versioned interpreter adapter | Golden traces match runtime values, phase, and line mapping |
| R02 | Explain a concept in multiple ways | Strategy library and selection contract | Same state tested with trace, visual, worked-example, guided-question, comparison, invariant strategies |
| R03 | Respect student choice | Preference controls/API | Student can override strategy, verbosity, and reset profile |
| R04 | Separate preferences from knowledge | Learner profile schema | Explicit preferences and inferred claims stored separately with provenance |
| R05 | Measure understanding | Reviewed assessment bank and outcome verifier | Unseen-input checks distinguish independent from assisted success |
| R06 | Adapt with uncertainty | Conservative concept/strategy updater | Sparse or contradictory evidence never creates confident mastery claims |
| R07 | Improve harness safely | Candidate/evaluation/promotion pipeline | No candidate affects production before recorded review and regression checks |
| R08 | Preserve source provenance | Dataset registry, pinned downloads, review records | Source revision, hash, license, split and intended use retained |
| R09 | Protect evaluation integrity | Dataset split and contamination audit | Related learners/problems/traces and overlapping source dialogues handled explicitly |
| R10 | Run on local Ollama | Measured runtime configuration | Required tasks complete within team-defined hardware/latency budget |
| R11 | Integrate with existing frontend | Typed client, errors, examples | End-to-end team UI test preserves snapshot identity through playback |
| R12 | Make profiles optional and controllable | Consent, access, export/reset/deletion | Opt-out works without persistent profiling; owner isolation tested |
| R13 | Reproduce experiments | Run manifests and reports | Same source/model/harness/settings/assessment versions identifiable |

Requirements can be amended through `NOTES.md` and `CHANGELOG.md`. User notes now target April 2027, mention a potential dedicated RTX 5090, and propose eventual expansion to hundreds of algorithms while starting small. Hardware purchase, exact scope, student age group, study size, hosting target and role assignments remain open.

## 4. Waterfall phases and gates

### Phase 0 — Baseline and data acquisition (current)

Inputs: existing fork, approved product boundaries, public-source recommendations.

Work: inventory implemented behavior; pin public-source revisions; download available material outside runtime RAG; retain original splits and attribution; record gated/partial sources; make acquisition reproducible and test checksum/path protections.

Deliverables: this plan, notes/change register, source lock, fetch command, local acquisition receipt, dataset use policy.

Exit gate G0: every source has an honest acquisition status; no raw source enters approved AVP training automatically; no secrets or student records are published. Known gaps: CSEDM account access and full EdNet acquisition.

### Phase 1 — Requirements and curriculum definition (planned)

Dependencies: G0; user notes and frontend/interpreter team input.

Work: choose presentation scope; define supported algorithms and AVP semantics; define knowledge components (indexing, assignment/copy, loop bounds, invariants, ordering, stability, complexity); identify prerequisites and common misconceptions. Specify accessibility, language, response-length preferences, data retention and opt-in behavior. Define a successful session from the student's perspective.

Deliverables: requirements v1, concept map, representative learner scenarios, prioritized backlog, owner/deadline table, initial risk register.

Exit gate G1: every must-have requirement has an owner, acceptance test and release target. Unknown choices remain explicitly open, not silently assumed. Instructor confirms the concept map and assessment intent.

### Phase 2 — Data preparation and assessment design (planned)

Dependencies: G1; source access for material actually selected.

Work: inspect schemas; normalize teaching moves and misconception examples without losing originals; preserve source IDs/licenses/splits. Use MathDial for pedagogical examples, OATutor for hint/scaffold structures, MRBench for response evaluation, and CSEDM/EdNet for offline learner-model research. Audit MathDial/MRBench overlap before any train/test combination. Create AVP examples grounded in interpreter traces; have an instructor review them.

Deliverables: normalized research schema, approved pedagogy examples, AVP assessment bank, independent held-out set, source-use manifest and contamination report.

Exit gate G2: distinguish synthetic students, real learners, model responses, and human annotations; no draft is represented as human-approved. Every assessment includes concept IDs, expected result/rubric, difficulty rationale, hint exposure and source provenance. Final-test questions are excluded from prompt tuning and training.

### Phase 3 — System and learner-model design (planned)

Dependencies: G2 and interpreter/frontend contract agreement.

Architecture: snapshot + student request + optional learner summary → strategy policy → teaching skill and reference selection → provider → answer → optional understanding check → verified observation → conservative profile update. Global candidate generation runs separately from the live request path.

Design a profile with explicit preferences, concept evidence, possible misconceptions, strategy observations, uncertainty, supporting event IDs and last-observed time. Do not assign fixed visual/auditory learner identities. Keep accessibility preferences distinct from inferred learning ability. Begin with transparent evidence counts/rules; compare Bayesian Knowledge Tracing only where assessments and concept labels support it. Do not present an uncalibrated score as a probability of mastery.

Define an event contract: pseudonymous owner/session IDs, concept/problem/trace IDs, strategy and version, request/answer IDs, assessment type, attempts, hint exposure, verified result, timestamps, consent state and experiment assignment. Link outcomes to the actual explanation seen. Time-on-task and non-use remain ambiguous observations.

Deliverables: architecture/data-flow diagrams, API/schema changes, threat/access model, profile update specification, strategy selection policy, retention/reset semantics, migration and rollback design.

Exit gate G3: designs trace to requirements; student overrides and no-profile operation are explicit; public/global content is separated from private learner state; no client can read another learner's profile.

### Phase 4 — Implementation and component verification (planned)

Dependencies: G3. Build in this order:

1. Interpreter adapter and golden trace fixtures.
2. Multiple explanation strategies plus explicit "try another explanation" selection.
3. Reviewed prediction/transfer checks and deterministic result verification where possible.
4. Event linkage, optional profile storage, student inspect/reset controls.
5. Conservative profile updater and strategy policy, with fixed-policy baseline.
6. Candidate skill rewrites/config changes in an isolated workspace; record rationale and evidence.
7. Evaluation comparison reports and reviewed promotion/rollback commands.

Use failing behavior tests before changing stateful logic. Mock model calls for routine CI, and budget small explicit live evaluations. Never execute text from feedback or downloaded datasets as code/instructions. Keep frontend changes limited to integration examples unless the frontend team requests more.

Deliverables: modules, schema migrations, typed client updates, unit/contract tests, fixtures, operator documentation.

Exit gate G4: each requirement's component tests pass; changed APIs regenerate schema/client; updates preserve actual prompt provenance; missing evidence uses a conservative default; failures cannot corrupt profiles or silently promote changes.

### Phase 5 — Integration and system verification (planned)

Dependencies: G4 and team frontend availability.

Work: connect the real UI; verify playback and question snapshots cannot drift; exercise all supported algorithms, different model providers, missing/conflicting state, malformed payloads, cancellation, unavailable models and concurrency. Test consent, ownership, deletion and retention across linked records. Compare fixed tutor and adaptive tutor on frozen cases. Review correctness and teaching usefulness independently of fluency.

Deliverables: integrated release candidate, test report, defect log, reproducible model/hardware latency report, accessibility and operator checklist.

Exit gate G5: no unresolved critical correctness/access defects; regression suite and builds pass; instructor review meets thresholds agreed in Phase 1. Timing and quality thresholds must be specified before final evaluation, not selected after seeing results.

### Phase 6 — Learning evaluation and controlled pilot (planned)

Dependencies: G5, participant consent and study design.

Work: begin with usability sessions; compare approved strategies on comparable tasks. Use prechecks, independent new-input questions and delayed transfer questions. Separate helpfulness ratings, assisted completion and demonstrated learning. Record exposure, assignment and missing outcomes. For randomized comparisons, define allocation, stopping criteria and sample-size rationale before analysis. Report uncertainty and attrition; a small presentation pilot is descriptive if underpowered.

Deliverables: pilot protocol, analyzed outcomes, subgroup failure review where justified by sample size, revised strategy recommendations, go/no-go report.

Exit gate G6: claims match evidence; no policy promoted on clicks or thumbs-up alone; student-level and task-level confounding addressed. A strategy win for one concept does not become a permanent universal learner label.

### Phase 7 — Release, monitoring and maintenance (planned)

Dependencies: G6 or an explicitly scoped non-adaptive presentation release after G5.

Work: deploy reviewed configuration, pin model/dataset/harness versions, document operational ownership, rehearse fallback and rollback. Monitor availability, factual errors, assessment failures, latency and profile-reset behavior. Collect optional feedback. Route proposed skill rewrites through the same tests and review gates; maintain a baseline comparison.

Deliverables: release tag, deployment/runbook, presentation script, known limitations, rollback package, maintenance backlog.

Exit gate G7: deployment reproduced, team frontend works, recovery demonstrated, handoff accepted by assigned owners. Ongoing changes reopen affected earlier gates.

### Phase 8 — Optional post-training research (deferred)

Dependencies: stable baseline, reviewed data, independent tests, hardware/export feasibility.

Train on reviewed question + code/state + selected teaching strategy + tutor response. Use whole algorithms for global reasoning and complete logical blocks for local steps. Compare untuned, harness-only, and tuned variants at the same task and resource settings. Keep AVP facts and dynamic state grounded at inference. Public math dialogue is supplemental pedagogy, not proof of AVP competence.

Exit gate G8: measurable benefit with no material regression on independent tasks; compatible Ollama deployment; source-use and attribution requirements resolved; adapter/model card published. If harness improvements suffice, do not train merely to add a feature.

## 5. Release scope and sequencing

No calendar dates are invented. The project owner fills them after Phase 1. The critical path is G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7. Post-training is optional after that foundation.

| Milestone | Scope | Owner / target |
|---|---|---|
| M0 | Existing grounded backend + public research collection + this plan | Delivered baseline; acquisition gaps documented |
| M1 | Presentation-ready integration, multiple approved explanations, static preferences | Backend + frontend + instructor; TBD |
| M2 | Optional learner profiles and verified checks; conservative adaptation | Backend + instructor; TBD |
| M3 | Controlled strategy experiments and reviewed global harness improvement | Experiment owner; TBD |
| M4 | Fine-tuned local model only if justified | ML owner; optional/TBD |

A useful M1 can ship before research personalization. Production authentication belongs to the team's deployment architecture and must be settled before persistent learner profiles are exposed.

## 6. Risks and decisions

| Risk | Mitigation / decision trigger |
|---|---|
| Fluent but incorrect algorithm explanations | Interpreter-grounded checks, instructor review, independent factual regression cases |
| Feedback preferences mistaken for learning | Separate satisfaction, assistance and transfer outcomes |
| Sparse learner data | Conservative defaults, uncertainty, student override; no confident style labels |
| Synthetic/public math data fails to transfer | Domain-specific AVP cases and separate measured evaluation |
| Source overlap leaks into evaluation | Keep original partitions and lineage; audit MRBench/MathDial shared dialogues |
| Latency/provider unavailability | Timeouts, visible errors, local baseline, opt-in fallback, measured hardware budget |
| Notes expand scope before presentation | Prioritize M1, log changes and revised phase impacts |
| Dataset access/license restrictions | Source registry and restricted research lanes; do not imply access has been obtained |
| Self-generated instructions regress behavior | Isolated candidates, full replay, reviewer decision, reversible versioned promotion |

Alternatives considered: fixed learner-style classification lacks a suitable evidence basis; direct online weight updates are hard to audit; importing all tutoring dialogue into runtime RAG mixes pedagogy with domain facts; a fixed strong tutor remains an essential baseline and potential release choice.

## 7. Proposed uncertainty-aware escalation (CR-002)

See [UNCERTAINTY_ROUTING.md](UNCERTAINTY_ROUTING.md) for the local-to-API routing experiment. It separates failure prediction from recovery benefit, verifies probability telemetry before using entropy, compares multiple uncertainty/verifier signals, and starts in shadow mode. This is proposed research; the live application still has provider-error fallback only. No new cloud routing or model instrumentation is enabled by this plan.

## 8. Change management and user notes

Add ideas freely in [NOTES.md](NOTES.md). Notes are proposed inputs, not implemented features. For each accepted change, add a `CR-###` entry to [CHANGELOG.md](CHANGELOG.md), identify affected requirements/phases, assess data/API/evaluation impact, update scope and plan version, and reopen only the relevant gates. Preserve previous decisions and reasons; never rewrite a historical result as if a later feature existed then.

Review points: before each phase gate, after interpreter/API changes, after pilot findings, and before any model/harness promotion. If a proposed change conflicts with the team's presentation work, record the tradeoff and defer it to a named milestone rather than expanding scope silently.
