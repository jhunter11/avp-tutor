"""Reference insertion-sort trace, not a general AVP interpreter.

Each immutable snapshot is AFTER its highlighted statement. The same trace is
used by the visual demo, tests, and seed training examples.
"""

import hashlib
import json

from tutor.models import ExecutionContext, ExecutionEvent

CODE = """fun insertion_sort(collection, size):
    for (i = 1, i < size, i += 1):
        key = collection[i]
        j = i - 1
        while (j >= 0):
            if (collection[j] > key):
                collection[j + 1] = collection[j]
                j = j - 1
            else:
                break
            end if
        end while
        collection[j + 1] = key
    end for
    return collection
end fun"""


def build_trace(values: list[int]) -> list[ExecutionContext]:
    if len(values) > 24 or any(type(v) is not int or abs(v) > 999 for v in values):
        raise ValueError("Use up to 24 integers between -999 and 999.")
    arr = list(values)
    frames = []
    events = []
    variables = {"size": len(arr)}
    run_id = "insertion-" + hashlib.sha256(json.dumps(values).encode()).hexdigest()[:12]

    def snapshot(line, kind, description, indices=(), details=None):
        events.append(
            ExecutionEvent(
                kind=kind,
                description=description,
                line=line,
                indices=list(indices),
                details=details or {},
            )
        )
        frames.append(
            ExecutionContext(
                algorithm="insertion_sort",
                code=CODE,
                current_line=line,
                phase="after",
                run_id=run_id,
                step=len(frames),
                variables=dict(variables),
                arrays={"collection": arr.copy()},
                recent_events=list(events[-3:]),
            )
        )

    snapshot(1, "start", "Input is ready. Sorting has not started.")
    for i in range(1, len(arr)):
        key = arr[i]
        variables.update(i=i, key=key)
        snapshot(3, "save", f"Saved collection[{i}] = {key} in key.", [i])
        j = i - 1
        variables["j"] = j
        snapshot(4, "pointer", f"Set j to {j}.", [j])
        while j >= 0:
            larger = arr[j] > key
            snapshot(
                6,
                "compare",
                f"Compared collection[{j}] = {arr[j]} > key = {key}: {larger}.",
                [j],
            )
            if not larger:
                snapshot(
                    10,
                    "break",
                    "The current value is not larger than key; stop shifting.",
                    [j],
                )
                break
            overwritten = arr[j + 1]
            arr[j + 1] = arr[j]
            snapshot(
                7,
                "shift",
                f"Copied {arr[j]} from index {j} to index {j + 1}, overwriting {overwritten} at index {j + 1}. Source index {j} is unchanged. key still holds {key}.",
                [j, j + 1],
                {
                    "source_index": j,
                    "destination_index": j + 1,
                    "copied_value": arr[j],
                    "overwritten_value": overwritten,
                    "saved_key": key,
                },
            )
            j -= 1
            variables["j"] = j
            snapshot(8, "pointer", f"Decreased j to {j}.", [j] if j >= 0 else [])
        arr[j + 1] = key
        snapshot(
            13,
            "insert",
            f"Placed saved key {key} at index {j + 1}. Prefix through index {i} is sorted.",
            [j + 1],
        )
    snapshot(15, "complete", "Returned the sorted collection.")
    return frames
