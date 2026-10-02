"""Original Codility-style exercise, with a deterministic reference oracle."""

BUGGY = """fun solution(values, target):
    i = 0
    while (i < length(values)):
        if (values[i] == target):
            return i
        end if
        return -1
        i += 1
    end while
    return -1
end fun"""

CORRECT = """fun solution(values, target):
    i = 0
    while (i < length(values)):
        if (values[i] == target):
            return i
        end if
        i += 1
    end while
    return -1
end fun"""

PROBLEM = {
    "id": "first-match",
    "title": "Find the first matching index",
    "description": "Return the zero-based index of the first value equal to target. Return -1 if target is absent. Check duplicates and an empty input.",
    "origin": "Original practice exercise in the style of Codility. No employer assessment content.",
    "buggy_code": BUGGY,
    "correct_code": CORRECT,
    "values": [4, 7, 2, 7],
    "target": 7,
}

CASES = [
    ("First element", [7, 4, 2], 7),
    ("Middle element", [4, 7, 2], 7),
    ("Last element", [4, 2, 7], 7),
    ("Absent target", [4, 2, 9], 7),
    ("Repeated target", [7, 4, 7], 7),
    ("Empty input", [], 7),
]


def expected_index(values, target):
    return next((i for i, value in enumerate(values) if value == target), -1)
