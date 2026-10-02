# V1 meeting brief

Prepared October 1, 2026. This is a local speaking draft and version proposal.
The team still owns product integration and approval of later milestones.

## A short opening

"I mapped the AVP RAG repository from Huy Tran: its code, retrieval, and model generation.
Then I built a small tutor harness around the student question, code, and execution evidence.
For V1, I chose an API model to test the tutoring interaction.
We can do that without hosting or training a local model.
I already knew the Gemini API setup from CSC 434.

This demo uses OpenRouter. The provider configuration also supports Gemini for a later comparison.
V1 uses fixed teaching instructions, and this document runs separately from the product frontend."

Use the live provider status and response metadata to support the provider claim.
Do not claim a Gemini live result from an OpenRouter response.

## Explain the example

"This practice question is parallel to the final AVP interface.
It has code input, program output, a visualization, and a place to ask the tutor.
Codility-style practice also supplies a problem description, which gives us a clear expected result.
We can exclude that description to test help with only the code and observed behavior.
The actual product will supply its own execution snapshots through the adapter."

Run the flawed first-match program.
Point to target `7`, expected index `1`, actual return `-1`, and the recorded index `0`.
Ask for a hint. Let the tutor connect the clue to the return statement.
Show the correction and rerun the tests.

## What connects to what

| Part | What it supplies | How V1 uses it |
|---|---|---|
| Upstream grammar and generated parser | AVP syntax structure | Parses the submitted demo code |
| Upstream sample algorithms | Examples of AVP source | Retains them for language and algorithm reference |
| Upstream ingestion and tracking | Code collection and change tracking | Preserves them for later corpus work |
| Upstream semantic retrieval | Optional BGE/FAISS code search | Keeps it available outside the lightweight demo |
| Upstream generation/API foundation | Retrieval and provider calls | Reuses the provider interface through the tutor harness |
| Fork snapshot contract | Code, line, phase, variables, arrays, events | Carries actual runner observations |
| Fixed tutoring skills | Hint, explain, debug, predict instructions | Selects one skill for each question |
| Exercise teaching pack | Intent, candidate confusion, effect, explanation method | Guides help on eight common first-match confusions |
| Coding reference retrieval | AVP rules and linear-search facts | Supplies bounded, sourced coding context |
| Teaching-method index | Probing, graduated hints, transfer-check proposal | Retrieves draft methods separately from coding facts |
| Optional local notes | Reviewed learner statements | Recalls relevant experience when the learner enables it |
| Model provider | Natural-language response | Returns an answer with model, source, and version metadata |

The verified upstream identity is `huytran088/avp_rag_system`.
The fork preserves the source history and attribution.
The V1 branch starts from the existing teaching-workflow revision `3726490`.

## Discuss the constraints

| Constraint | Why it matters | V1 choice | Later evidence needed |
|---|---|---|---|
| Local concurrency | Shared inference increases waiting and memory demand | One active request | Measure concurrent users on selected hardware |
| Local model quality | Small models can miss facts or reveal answers | Hosted provider | Compare reviewed answers on frozen cases |
| Training resources | Review, hardware, training, and evaluation cost effort | Skills and retrieval first | Review AVP targets before training |
| API tradeoffs | Access, quotas, privacy, latency, and cost affect operation | Explicit provider | Measure latency, tokens, failures, and cost |
| Memory | Experience can preserve useful context or mistakes | Reviewed notes | Validate corrections and measure transfer |
| Teaching-data transfer | Mathematics and coding have different facts | Separate methods and facts | Review coding interactions |

The repository contains earlier local-model and Gemini development observations in `docs/verification.md`.
Those dated examples do not establish a current comparative benchmark.
This version does not claim that an API provider is always more intelligent or faster than a local model.

## Proposed versions through the April deadline

| Version | Focus | Evidence before advancing |
|---|---|---|
| V1, now | One exercise, document, fixed skills, retrieval, provider, optional notes | Actual execution, useful tutoring, startup checks |
| V2, next milestone | Production snapshot adapter and a small supported algorithm set | Interpreter conformance and integration tests |
| V3, later term | Reviewed cases, semantic retrieval, learning measures, provider comparisons | Human rubric, transfer checks, resource measurements |
| Final research version | Controlled self-scaffolding proposals and optional post-training | Replay tests, reviewed promotion, rollback, and independent evaluation |

Confirm the dates with the team. This table sets scope, not a new course schedule.
Self-scaffolding means proposing and evaluating harness changes before promotion.
It should not silently rewrite the active tutor after a conversation.

## Claims the demo can support

The standalone shape works with actual edited AVP in a bounded runner.
The harness attaches code, observed state, selected skills, and relevant notes to a question.
The provider response can show that hosted inference works through that harness.
The optional note store can retain reviewed context without saving API keys or changing model weights.

The demo does not establish improved learning, semantic transfer quality, local-model capacity, or a trained AVP model.
Those results require the later evaluations above.
