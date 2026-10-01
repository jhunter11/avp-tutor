# Fixed teaching pack checks

The displayed problem is a first-match linear search.
Return the first zero-based index equal to the target. Return minus one after every item fails.

The pack covers seven likely confusion patterns. It does not cover every possible misunderstanding.

| Confusion | Example learner question | Effect | Teaching method |
|---|---|---|---|
| Early return | Why stop early? | Later matches never run | Trace a later match |
| Index versus value | Return the number? | Wrong result type | Label values with indices |
| Duplicates | Which match? | Wrong matching position | Compare first and second matches |
| Loop bounds | Include the final index? | Skipped item or invalid access | Trace the final index |
| Empty input | No items? | Loop never enters | Check the initial condition |
| Absent target | Return zero? | Absence overlaps index zero | Compare missing and first-position cases |
| Loop progress | Why hang? | Same step repeats | Track the index change |

The teaching plan separates the learner request from candidate confusions.
It records actual interpreter observations separately from those hypotheses.
The response selects a method and includes a follow-up check appropriate to its mode.

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

The matrix caught a tie between the generic word `return` and the phrase `not found`.
Phrase length now contributes to ranking. The regression test preserves the absence case.
Live OpenRouter requests check useful hints and debug explanations against observed execution.
These checks establish functional behavior for this question. They are not an independent teaching-quality benchmark.

The question box uses Enter to submit and Shift+Enter for a newline.
It clears on submission. A failed request restores the question unless a new draft exists.
Up and Down recall the last ten submitted questions within the page session.
