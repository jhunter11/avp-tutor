# AI tutor — team meeting brief

Prepared 2026-09-24. This brief distinguishes the current backend from the proposed first versions. It is a speaking guide, not a claim that the proposals have been implemented.

## A 45-second introduction

“We already have a backend that can answer questions using the algorithm step, variables and code the student is looking at. My next goal is to make it behave more like a tutor: find the misunderstanding, explain it another way, and check whether the student can apply the idea independently. We can also use that evidence to personalize future help. The research side is to test which context, prompts and models actually improve the result. Our existing frontend remains the product; the extra interface is just a place to demonstrate and test these capabilities.”

## The fifteen ideas, in conversational and technical terms

| Idea | How to say it | What makes it work | Current status before this implementation |
|---|---|---|---|
| Grounded explanations | “It should explain what actually happened in our program.” | Immutable interpreter snapshots, explicit before/after phase, structured trace facts and scoped consistency checks. | Snapshot API and scoped copy checks exist; external interpreter adapter missing. |
| Predict and check | “Before the next step, let the student guess, then discuss why.” | Server-owned questions and expected values derived from reference traces; submitted answers verified separately from LLM prose. | Prediction prompts exist; scored loop proposed. |
| Misconceptions and hints | “If they think copying is swapping, address that exact confusion.” | Limited known misconception mappings, a hint ladder, and assistance recorded with the outcome. | Basic hint mode exists; structured ladder proposed. |
| Different explanations | “Try the same idea with real values, a comparison, or a visual explanation.” | Versioned teaching strategies and an explicit student override; facts stay the same. | Four modes and six selectable strategies now exist; learning benefit still needs evaluation. |
| Transfer checks | “Could they solve it with different numbers without help?” | New-input assessments and separation of independent versus assisted success. | Development examples exist; student assessment workflow proposed. |
| Prerequisite checks | “Maybe the difficulty is indexing, not sorting.” | Small concept graph with diagnostic questions for prerequisites. | Proposed. |
| What-if lab | “Change one rule and see why the behavior changes.” | Controlled reference execution of approved variants, preserving element identities for stability comparisons. | Proposed; not arbitrary AVP execution. |
| Fading worked examples | “Show one, help with one, then let them try.” | Worked, partially completed and independent stages with explicit help exposure. | Proposed. |
| Learner profiles | “Remember evidence about what they know, without labeling their intelligence.” | Optional pseudonymous profile, explicit preferences, supporting observations and reset. | Interaction feedback exists; persistent learner model proposed. |
| Spaced review | “Bring back an important idea after a delay.” | Review dates derived from assessment outcomes; no claim of an optimal schedule. | Proposed. |
| Instructor tools | “Let the instructor define the concepts and check our teaching material.” | Versioned curriculum, prerequisite validation, review status and assessment auditing. | Source material and draft review fields exist; consolidated tooling proposed. |
| Responsive, accessible controls | “Students can change the amount of detail and stop waiting.” | Labelled controls, keyboard access, readable state, cancellation and response timing. | Test UI has several controls; learning lab integration proposed. |
| Harness experiments | “Try a better instruction, and prove it did not break other answers.” | Candidate configs, identical evaluation cases, comparison report and reviewed promotion. | Candidate proposer and evaluation runner exist; comparison workflow to extend. |
| Uncertainty routing | “When local output looks risky, check it or ask a stronger model.” | Probability telemetry, correctly named uncertainty statistics, shadow routing and explicit cloud opt-in. | Basic logprob probe succeeded; quality routing proposed. |
| Fine-tuning | “If a teaching problem keeps recurring, use reviewed examples to train for it.” | Approved-data export, grouped splits, readiness checks and later trainer/model selection. | Export exists; no trained model. |

## A concrete student story

A student watches insertion sort copy an 8 over a 3 and asks whether the 3 was lost. The tutor points to the saved key, explains the copy, and offers a comparison with a swap. It then presents a different input and asks where a value is preserved. If the student answers independently, that is evidence about this concept. If they need three hints, the successful answer is recorded as assisted. Both can be useful learning experiences, but we should not treat them as equivalent evidence of mastery.

## How the pieces connect

Question + exact execution snapshot → teaching strategy → relevant notes → model answer → optional independent check → evidence in an optional learner profile.

A separate process evaluates changes to teaching instructions and routing. It does not rewrite the live tutor after each thumbs-up or immediately train on student conversations.

## What we need from the team

- An interpreter adapter that captures code, highlighted line, phase, variables, arrays and recent state transitions when a question is asked.
- Agreement on a small initial algorithm/concept set; hundreds of algorithms need conformance fixtures and curriculum coverage rather than names alone.
- Frontend-owned controls for explanation choice, consent and feedback, with the answer attached to the step that generated it.
- A reviewer for factual and pedagogical targets, and a definition of the learning outcomes we want to measure.
- A practical deployment decision: local hardware, model, latency budget and whether hosted fallback is allowed.

## Questions the team might ask

**“Does it learn automatically from students?”**
Not currently. The intended first version updates a transparent evidence profile from verified checks and proposes global changes for review. That is different from changing model weights.

**“Does a correct answer mean the student learned?”**
It is one observation. New-input and delayed checks give stronger evidence than repeating an answer the tutor just revealed.

**“Can entropy tell us when a model is wrong?”**
It is a hypothesis to test. Different valid wording can raise uncertainty, and wrong answers can be confident. We compare it with verifiers and actual outcomes.

**“Are public datasets enough?”**
They supply tutoring patterns and evaluation ideas. Our language still needs interpreter-grounded examples and instructor review.

**“Do we need a new frontend?”**
No. The backend exposes contracts the product frontend can use. The temporary lab is for demonstrations and tests.

**“What would be a credible April presentation?”**
A complete student interaction on a small supported set: faithful state explanation, alternative strategy, independent check, visible evidence and honest limitations. Research features can be demonstrated as experiments without claiming proven learning gains.

## Workflow improvement pass

The backend now returns its teaching decision, scoped evidence checks, bounded syntax-checked examples and exact prompt hash. The testing UI exposes strategy choice and preparation details. See [the runnable workflow](../workflow.md) for a meeting demonstration. None of this constitutes independent AVP execution, a validated learner profile, or automatic self-improvement.
