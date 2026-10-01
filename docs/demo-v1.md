# AVP Tutor V1 demo

Prepared October 1, 2026. This page describes the standalone meeting demo.

The demo shows one complete tutoring interaction on an original exercise in the style of Codility.
The student writes AVP, runs it, inspects the output, and asks about the solution.
The product frontend remains a later integration step.

## Start the document

Use the repository startup guide to select a provider and load an existing local credential file.
The ASGI target is `demo_v1.app:app`. The local demo address is `http://127.0.0.1:8771/`.

For a development launch from the repository root:

```sh
uv sync --frozen
uv run uvicorn demo_v1.app:app --host 127.0.0.1 --port 8771
```

The demo honors `LLM_PROVIDER` and that provider's model variables.
Set `AVP_DEMO_ENV` to load an existing local environment file without copying it.
The provider and model appear in the document.
Configuration status does not prove that a model can return an answer.

## Present the interaction

1. Open the document and keep the flawed draft.
2. Show the custom input: `[4, 7, 2, 7]`, target `7`.
3. Compare expected index `1` with actual output `-1`.
4. Show the recorded return at line 7, with `i = 0`.
5. Select Hint and ask, "Why does my solution fail when the target is later in the array?"
6. Read the clue and inspect References and attached context.
7. Move `return -1` outside the loop, or load the corrected draft.
8. Run the code again and show all six tests passing.
9. Ask about repeated targets or an empty input to show another teaching choice.

The flawed draft passes four of the six fixed tests.
The corrected draft passes all six tests.
The custom input is separate from that test count.

Uncheck Send problem description to tutor to show the interface without a supplied problem contract.
The tutor then receives observed outputs without expected results or pass labels.
It must ask about intent before asserting the desired behavior.

## The fixed harness

The server prepares this sequence for each question:

```text
Edited AVP + input
    -> bounded execution and test observations
    -> question intent and candidate confusion
    -> selected skill + coding references + teaching methods
    -> optional relevant learner notes
    -> configured model
    -> answer with source and version metadata
```

The harness contains four selected skills: hint, explain, debug, and predict.
The server loads their fixed configuration from `demo_v1/harness.json`.
The demo does not expose the existing feedback or candidate-generation routes.
The model cannot edit skills, retrieve arbitrary files, run tools, or train itself.

`demo_v1/teaching.json` contains eight candidate confusions for this exercise.
Each record names its effect on the solution and a suitable explanation method.
Keyword matches and observed outputs support teaching choices. They do not diagnose a student's ability.
Definition questions can have no candidate confusion.
The runner records actual condition array reads and return scope to support bounded result diagnoses.
When the problem description is absent, retrieval excludes the exercise contract and the tutor asks about intended output.

Read [the configuration checks](demo-teaching-checks.md) and [the live review](teaching-config-review-2026-10-01.md) before presenting.

## Retrieval and teaching data

The coding facts come from `knowledge/avp.md` and `knowledge/linear-search.md`.
The existing lexical retriever selects up to three relevant sections.

The separate pedagogy index contains three draft method cards.
It uses normalized local TF-IDF vectors and cosine similarity to select up to two cards.
This is a small term-based vector index. It is not a semantic embedding model.

MathDial informs probing questions about a described confusion.
OATutor informs hints that progress through dependencies.
The transfer-check card is an original project proposal.
The cards retain source revisions, source URLs, attribution, and license labels in `demo_v1/pedagogy.json`.

These coding adaptations need instructor review and evaluation.
Vectorizing a teaching method does not prove that it transfers from mathematics to coding.
No raw mathematical answer serves as coding evidence.
MRBench remains evaluation material. CSEDM and EdNet remain documentation-only acquisitions in the existing collection.

## Optional memory

Save a short learning note only after reviewing it.
Enable Use my learning notes to include up to two relevant notes in later questions.
The demo stores notes, dates, and random record IDs. It does not save conversations automatically.
Notes remain user reports. They do not establish mastery or change model weights.

| Operating system | Default note store |
|---|---|
| Windows | `%LOCALAPPDATA%/avp-tutor-v1/learner.sqlite3` |
| macOS | `~/Library/Application Support/avp-tutor-v1/learner.sqlite3` |
| Linux | `$XDG_DATA_HOME/avp-tutor-v1/learner.sqlite3`, or `~/.local/share/avp-tutor-v1/learner.sqlite3` |

Use `AVP_DEMO_MEMORY_PATH` to select another private local location.
Keep the note store and credential files outside the repository.
The note writer rejects recognized key patterns and credential assignments.
Delete a note through the document when it no longer applies.
Reset demo clears the page's conversation and restores the flawed draft. It preserves saved learning notes.

## Execution boundary

The runner interprets the submitted syntax tree from the repository's ANTLR parser.
It supports one `solution(values, target)` function with bounded integer inputs and read-only arrays.
Supported statements include scalar assignments, `+=`, `-=`, `while`, `if`, and integer `return`.
Expressions include array access, `length`, comparisons, Boolean operations, parentheses, `+`, and `-`.
The runner rejects unsupported features and stops at 2,000 operations or 256 snapshots per input.
It never uses Python `eval` or executes host commands.

This is a demo subset with its own explicit semantics.
The team's production AVP interpreter still needs an adapter and conformance tests.
Passing the displayed tests proves those results in this runner. It does not prove general correctness or student learning.
