# Linear search

## The search contract

Inspect input values from index zero. Return the first index whose value equals the target. Return -1 after all values fail the comparison. An empty input has no matching index. Duplicate targets require the first matching index.

## Return and loop progress

A return ends the function. A failed comparison at one index does not prove that the target is absent from the remaining input. If a return occurs before an index update, that update never executes. Use the recorded return line and index to diagnose the current run.

## Positions and values

The demo uses zero-based indices. For values = [4, 7, 2], index 0 stores 4 and index 1 stores 7. The target value 7 has first matching index 1. The first-match contract asks for that index, not the target value or a position counted from one.

## Array length and bounds

In the demo runner, length(values) counts the input values. Three values have length 3 and valid indices 0, 1, and 2. The last valid index is length minus one. An empty array has length zero and no valid index. These are explicit demo rules. The production interpreter still needs conformance checks.

## Testing a search

Check a match at the first, middle, and last index. Also check an absent target, duplicates, and an empty input. A correct result for one input does not prove correctness for all inputs. These cases are project-authored guidance for the demo exercise.
