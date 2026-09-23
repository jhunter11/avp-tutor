"""Rebuild synthetic draft fixtures from deterministic traces, never student logs."""

import json
from pathlib import Path

from tutor.demo import build_trace

ROOT = Path(__file__).resolve().parent.parent


def row(
    id, algorithm, question, answer, facts, context=None, mode="explain", history=None
):
    request = {"question": question, "mode": mode}
    if context:
        request["context"] = context
    else:
        request["context"] = {"algorithm": algorithm}
    if history:
        request["history"] = history
    return {
        "id": id,
        "algorithm": algorithm,
        "program_id": algorithm + "-reference-v1",
        "trace_id": context["run_id"] if context else id,
        "provenance": "synthetic-draft",
        "review_status": "draft",
        "reviewed_by": "",
        "request": request,
        "answer": answer,
        "expected_facts": facts,
    }


def trace_rows(prefix, inputs):
    rows = []
    for number, values in enumerate(inputs):
        frames = build_trace(values)
        frame = next(f for f in frames if f.recent_events[-1].kind == "shift")
        key = frame.variables["key"]
        event = frame.recent_events[-1]
        origin, destination = event.indices
        copied = frame.arrays["collection"][destination]
        context = frame.model_dump()
        rows.append(
            row(
                f"{prefix}-{number}-saved-key",
                "insertion_sort",
                "Did we lose the value that was overwritten?",
                f"The overwritten array position is not the only place the value was stored: key still holds {key}. This step copied {copied} from index {origin} to index {destination} to make room. The algorithm inserts the saved key after it finishes shifting larger values.",
                [
                    f"key remains {key}",
                    f"{copied} was copied to index {destination}",
                    "shift is a copy, not a swap",
                ],
                context,
            )
        )
        rows.append(
            row(
                f"{prefix}-{number}-hint",
                "insertion_sort",
                "Give me a hint about why we keep key.",
                "Look at the key variable next to the array. What value does it still hold after the highlighted assignment overwrites an array position?",
                [
                    "direct attention to saved key",
                    "ask a guiding question instead of giving a full solution",
                ],
                context,
                mode="hint",
            )
        )
        rows.append(
            row(
                f"{prefix}-{number}-follow-up",
                "insertion_sort",
                "So was that a swap?",
                f"No. The highlighted assignment copied {copied} one position right; it did not exchange two array values. key separately holds {key} until the insertion step fills the open position.",
                ["not a swap", f"saved key is {key}"],
                context,
                history=[
                    {"role": "user", "content": "Why are there two equal numbers?"},
                    {
                        "role": "assistant",
                        "content": "A shift temporarily copies a value to the neighboring position.",
                    },
                ],
            )
        )
    return rows


CONCEPTS = [
    (
        "insertion_sort",
        "What is the invariant?",
        "At the start of iteration i, the prefix before i is sorted. The algorithm saves the next value, shifts larger values, and inserts the saved key. After that insertion, the sorted prefix includes index i.",
        [
            "sorted prefix at iteration boundaries",
            "do not assert permutation during a shift",
        ],
    ),
    (
        "insertion_sort",
        "Is it always quadratic?",
        "No. In this implementation an already sorted array needs only one failed inner comparison per insertion, so the running time is linear. Reverse order requires a growing number of shifts and takes quadratic time.",
        ["linear best case", "quadratic worst case"],
    ),
    (
        "insertion_sort",
        "What happens for an empty array?",
        "There is nothing to insert. The outer loop does not run and the empty collection is returned; it is already sorted.",
        ["no outer iterations", "empty is sorted"],
    ),
    (
        "insertion_sort",
        "Can equal numbers change order?",
        "This implementation shifts only values strictly greater than key. Equal values are not shifted past the new key, which preserves their original relative order. That property is called stability.",
        ["strict greater comparison", "stable"],
    ),
    (
        "binary_search",
        "Can we use binary search on an unsorted array?",
        "Not reliably. Discarding half the array is justified by its sorted order. Without that order, the discarded half can still contain the target.",
        ["requires sorted input", "discard can lose target"],
    ),
    (
        "binary_search",
        "Does it always return the first duplicate?",
        "A basic binary search can return any matching occurrence. Finding the first duplicate requires a variant that continues searching the left side after a match.",
        ["not necessarily first", "variant needed"],
    ),
    (
        "binary_search",
        "Why logarithmic time?",
        "Each comparison removes about half the remaining candidates. Only about log2(n) halvings are needed to reduce n candidates to one, assuming constant-time indexed access.",
        ["halves interval", "random access assumption"],
    ),
    (
        "bubble_sort",
        "Is bubble sort linear on sorted input?",
        "Only if the implementation tracks swaps and stops after a full pass with none. A version that always runs all passes still performs quadratic work on sorted input.",
        ["early-exit optimization required"],
    ),
    (
        "bubble_sort",
        "What is settled after a pass?",
        "In an ascending left-to-right pass, the largest value in the unsorted region reaches its right boundary. That position is settled, but the rest can still need more passes.",
        ["largest at right boundary", "not entire array sorted"],
    ),
    (
        "selection_sort",
        "Why is selection sort not stable?",
        "The usual version swaps the minimum with a potentially distant position. That swap can move one equal element past another, changing their original order.",
        ["distant swap can reorder equals"],
    ),
    (
        "selection_sort",
        "Does sorted input avoid the comparisons?",
        "The standard implementation still scans the remaining suffix to select its minimum on every pass. It therefore makes quadratic comparisons even if the input was already sorted.",
        ["quadratic comparisons even sorted"],
    ),
    (
        "merge_sort",
        "Why do we need extra space?",
        "A standard array merge sort uses a temporary buffer to combine two sorted ranges without overwriting values that are still needed. That buffer requires linear auxiliary storage.",
        ["standard array variant", "linear buffer"],
    ),
    (
        "merge_sort",
        "What makes merging correct?",
        "The two input ranges are already sorted. Choosing the smaller front value appends the smallest remaining candidate, so the output prefix stays sorted as the merge proceeds.",
        ["inputs sorted", "smallest front value"],
    ),
    (
        "avp",
        "The parser accepted my code. Does that mean it works?",
        "It means the code passed the grammar's syntax checks. It does not prove correct variable usage, safe array indices, runtime behavior, or a correct algorithm. Those need additional checks and execution tests.",
        ["syntax is not execution", "no correctness guarantee"],
    ),
]


def main():
    seed = trace_rows("seed", [[2, 7, 9, 4], [5, 2, 4], [3, 3, 1], [0, -2, 1]])
    seed += [row(f"seed-concept-{i}", *case) for i, case in enumerate(CONCEPTS[:7])]
    benchmark = trace_rows(
        "eval",
        [
            [8, 3, 6],
            [9, 8, 7],
            [4, 1, 4],
            [10, 0],
            [-1, -5, 2],
            [7, 3, 5, 1],
            [6, 2, 6, 2],
            [20, 12, 15],
            [11, 8, 9, 10],
            [3, 2, 1, 0],
            [100, -100],
            [5, 4, 6, 3],
        ],
    )
    benchmark += [row(f"eval-concept-{i}", *case) for i, case in enumerate(CONCEPTS)]
    for name, records in [("seed_examples", seed), ("benchmark", benchmark)]:
        (ROOT / "training" / f"{name}.jsonl").write_text(
            "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
        )
        print(f"{name}: {len(records)} draft examples")


if __name__ == "__main__":
    main()
