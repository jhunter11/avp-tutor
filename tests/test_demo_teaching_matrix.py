"""Check the small question-specific teaching configuration against actual code mistakes."""

import json

import pytest

from demo_v1.exercise import BUGGY, CORRECT
from demo_v1.service import AskRequest, prepare

LAST_MATCH = """fun solution(values, target):
    i = 0
    found = -1
    while (i < length(values)):
        if (values[i] == target):
            found = i
        end if
        i += 1
    end while
    return found
end fun"""


@pytest.mark.parametrize("confusion,question,code,values,target", [
    ("early-return", "Why does it stop early when the target is later?", BUGGY, [4, 7, 2], 7),
    ("index-vs-value", "Should I return the value or its position?", CORRECT.replace("return i", "return values[i]"), [4, 7, 2], 7),
    ("duplicates", "Why is the repeated target giving the last match?", LAST_MATCH, [7, 4, 7], 7),
    ("loop-bounds", "Why does this off-by-one bound read outside the array?", CORRECT.replace("i < length", "i <= length"), [4, 2], 7),
    ("empty-input", "What should happen for empty input?", CORRECT, [], 7),
    ("absent-target", "Should I return zero when the target is not found?", CORRECT.replace("return -1", "return 0"), [4, 2], 7),
    ("loop-progress", "Why does the loop hang without an increment?", CORRECT.replace("        i += 1\n", ""), [4, 7], 7),
])
def test_confusion_effect_and_teaching_method_match_supplied_case(confusion, question, code, values, target):
    request = AskRequest(code=code, values=values, target=target, question=question, mode="debug")
    messages, facts, methods, _notes, run = prepare(request)
    payload = json.loads(messages[-1]["content"])
    plan = payload["teaching_plan"]
    assert plan["intent"] == "minimal diagnosis and correction"
    assert plan["candidate_confusions"][0]["id"] == confusion
    assert plan["candidate_confusions"][0]["impact"]
    assert plan["explanation_method"] and plan["observations"]
    assert len(plan["candidate_confusions"]) <= 2
    assert len(facts) <= 3 and len(methods) <= 2
    assert payload["execution_context"]["code"] == code
    case = run["cases"][0]
    if confusion == "empty-input":
        assert case["passed"] and case["actual"] == -1
    else:
        assert not case["passed"]
    assert len(json.dumps(messages)) < 18000


def test_each_mode_has_its_own_fixed_skill_and_hint_does_not_use_debug_instructions():
    from demo_v1.service import CONFIG
    from harness.config import skill_text
    assert len(set(CONFIG.skills.values())) == 4
    for mode in ["hint", "debug", "explain", "predict"]:
        request = AskRequest(code=BUGGY, values=[4, 7, 2], target=7, question="Why does it fail later?", mode=mode)
        messages, _facts, methods, *_ = prepare(request)
        assert skill_text(CONFIG, mode) in messages[0]["content"]
        assert methods
    hint = skill_text(CONFIG, "hint")
    assert "Do not show the corrected program" in hint
