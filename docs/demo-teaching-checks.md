# Fixed teaching pack checks

The displayed problem is a first-match linear search.
Return the first zero-based index equal to the target. Return minus one after every item fails.

The pack covers eight likely confusion patterns. It does not cover every possible misunderstanding.

| Confusion | Example learner question | Effect | Teaching method |
|---|---|---|---|
| Early return | Why stop early? | Later matches never run | Trace a later match |
| Index versus value | Return the number? | Wrong result type | Label values with indices |
| Zero-based indexing | Why index 1 instead of position 2? | Counting starts at the wrong label | Label positions from zero |
| Duplicates | Which match? | Wrong matching position | Compare first and second matches |
| Loop bounds | Include the final index? | Skipped item or invalid access | Trace the final index |
| Empty input | No items? | Loop never enters | Check the initial condition |
| Absent target | Return zero? | Absence overlaps index zero | Compare missing and first-position cases |
| Loop progress | Why hang? | Same step repeats | Track the index change |

The teaching plan has four parts: the request, candidate confusion, effect, and explanation method.
It records actual interpreter observations separately from those hypotheses.
Each answer's context panel shows the question focus, selection basis, runner observations, and method.

Result questions use observed evidence when a bounded rule identifies a supported cause.
The runner records actual condition array reads and the loop depth of a return.
This distinguishes a return inside the loop from a loop that excludes the final index.
It also avoids counting an array read that a Boolean expression skips.

Definition questions can have no candidate confusion.
A request about `length(values)` receives the length reference without assuming an indexing mistake.
A vague follow-up can use the last student question as a topic hint.
The latest code and execution still control factual claims.

When the problem description is absent, result questions ask about intended output.
The model receives no expected outputs, pass labels, or exercise-contract references in that mode.

## Small retrieval configuration

Four fixed skills select Hint, Explain, Debug, and Predict behavior.
Local lexical retrieval supplies at most three fact sections.
Normalized TF-IDF retrieval supplies at most two teaching-method cards.
The method cards include MathDial and OATutor source links, revisions, and license notes.
Their coding adaptations still need instructor review.

No embeddings, vector service, training run, or autonomous prompt rewrite runs at startup.

The response includes the selected case, execution hash, prompt hash, pack version, and source cards.
These fields help inspect the exact inputs behind an answer.
They do not establish that an explanation improves learning.

## Verification scope

The deterministic teaching matrix uses seven distinct code variants and learner questions.
It checks confusion selection, intent, consequences, method, and bounded context size.
It runs each variant through the actual interpreter.
Separate tests cover all four skills and 120 randomized first-match examples.

The language regressions cover realistic paraphrases, zero-based counting, definitions, and vague follow-ups.
Negative controls include a wrong comparison, a short loop bound, and a skipped Boolean operand.
Phrase length contributes to ranking. Word boundaries prevent `value` from matching `values`.
Execution evidence can replace generic keyword matches for result questions.
Live OpenRouter requests check all four modes against observed execution.
These checks establish functional behavior for this question. They are not an independent teaching-quality benchmark.

See [the dated review](teaching-config-review-2026-10-01.md) for answers, failures, corrections, and limits.

The question box uses Enter to submit and Shift+Enter for a newline.
It clears on submission. A failed request restores the question unless a new draft exists.
Up and Down recall the last ten submitted questions within the page session.
