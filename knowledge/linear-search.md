# Linear search

## The search contract

Inspect input values from index zero. Return the first index whose value equals the target. Return -1 after all values fail the comparison. An empty input has no matching index. Duplicate targets require the first matching index.

## Return and loop progress

A return ends the function. A failed comparison at one index does not prove that the target is absent from the remaining input. If a return occurs before an index update, that update never executes. Use the recorded return line and index to diagnose the current run.

## Testing a search

Check a match at the first, middle, and last index. Also check an absent target, duplicates, and an empty input. A correct result for one input does not prove correctness for all inputs. These cases are project-authored guidance for the demo exercise.
