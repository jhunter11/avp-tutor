import random

from demo_v1.exercise import BUGGY, CORRECT, expected_index
from demo_v1.runtime import execute


def test_actual_draft_executes_and_fix_changes_output():
    bad = execute(BUGGY, [4, 7, 2], 7)
    good = execute(CORRECT, [4, 7, 2], 7)
    assert bad["actual"] == -1 and good["actual"] == 1
    assert bad["frames"][-1]["current_line"] == 7
    assert bad["frames"][-1]["variables"]["i"] == 0
    assert all(f["phase"] == "after" and f["code"] == BUGGY for f in bad["frames"])


def test_edited_avp_matches_independent_first_match_oracle():
    rng = random.Random(42)
    for _ in range(120):
        values = [rng.randrange(-3, 4) for _ in range(rng.randrange(15))]
        target = rng.randrange(-3, 4)
        result = execute(CORRECT, values, target)
        assert not result["error"]
        assert result["actual"] == expected_index(values, target)


def test_runtime_limits_no_host_calls_and_bounds():
    for code, fragment in [
        (
            "fun solution(a, t):\n    while (true):\n        t += 1\n    end while\n    return t\nend fun",
            "limit",
        ),
        ("fun solution(a, t):\n    return a[-1]\nend fun", "bounds"),
        ("fun solution(a, t):\n    return open(t)\nend fun", "Only length"),
        ("fun solution(a, t):\n    return False\nend fun", "integer index"),
        ("fun solution(a, t):\n    return 2 ** 100\nend fun", "outside"),
        ("fun solution(a, t):\n    a[0] = 1\n    return 0\nend fun", "read-only"),
    ]:
        result = execute(code, [1], 1)
        assert fragment in result["error"]
        assert len(result["frames"]) <= 256


def test_snapshot_immutable_and_boolean_not_an_index():
    result = execute(CORRECT, [1, 2], 2)
    assert result["frames"][0]["variables"]["i"] == 0
    assert result["frames"][-1]["variables"]["i"] == 1
    result["frames"][-1]["arrays"]["values"][0] = 9
    assert result["frames"][0]["arrays"]["values"] == [1, 2]
