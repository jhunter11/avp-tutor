"""Small teaching choices grounded in the question and recorded execution."""

import json
import re

from demo_v1.retrieval import ROOT

PACK = json.loads((ROOT / "teaching.json").read_text(encoding="utf-8"))
CARDS = {card["id"]: card for card in PACK}


def ranked_cards(question):
    scores = []
    for card in PACK:
        score = sum(
            len(term.split())
            for term in card["question_terms"]
            if re.search(
                r"(?<![a-z0-9_])" + re.escape(term) + r"(?![a-z0-9_])", question
            )
        )
        if score:
            scores.append((score, card))
    return [card for _, card in sorted(scores, key=lambda item: -item[0])][:2]


def execution_evidence(request, case):
    comparisons = []
    for frame in case["frames"]:
        event = frame["recent_events"][-1]
        if event["kind"] != "condition":
            continue
        for read in event["details"].get("array_reads", []):
            comparisons.append(
                {
                    **read,
                    "condition_result": event["details"].get("value"),
                    "line": frame["current_line"],
                }
            )
    frame = case["frames"][-1] if case["frames"] else None
    returned = bool(frame and frame["recent_events"][-1]["kind"] == "return")
    evidence = {
        "actual": case["actual"],
        "error": case["error"],
        "return_line": frame["current_line"] if returned else None,
        "return_loop_depth": frame["recent_events"][-1]["details"].get("loop_depth", 0)
        if returned
        else None,
        "return_reads": frame["recent_events"][-1]["details"].get("array_reads", [])
        if returned
        else [],
        "compared_indices": sorted({c["index"] for c in comparisons}),
        "comparison_samples": comparisons[:8],
        "limits": "Actual array reads in recorded conditions. These bounded heuristics are not full semantic analysis or a learner diagnosis.",
    }
    if request.include_problem:
        evidence["expected"] = case["expected"]
    return evidence


def supported_confusion(request, case, evidence):
    error = case["error"] or ""
    if "limit" in error:
        return "loop-progress"
    if "bounds" in error:
        return "empty-input" if not case["values"] else "loop-bounds"
    if not request.include_problem or case["passed"] or error:
        return None
    actual, expected = case["actual"], case["expected"]
    if (
        actual == -1
        and evidence["return_loop_depth"]
        and case["target"] in case["values"]
    ):
        matches = {
            i for i, value in enumerate(case["values"]) if value == case["target"]
        }
        if evidence["compared_indices"] and matches - set(evidence["compared_indices"]):
            return "early-return"
    if actual == case["target"] and actual != expected and evidence["return_reads"]:
        return "index-vs-value"
    matches = [i for i, value in enumerate(case["values"]) if value == case["target"]]
    if len(matches) > 1 and actual == matches[-1] and actual != expected:
        return "duplicates"
    if expected == -1 and actual == 0:
        return "absent-target"
    return None


def choose(request, case):
    question = request.question.lower().replace("−", "-")
    evidence = execution_evidence(request, case)
    candidates = ranked_cards(question)
    basis = "student question" if candidates else "no specific match"
    focus = candidates[0]["title"] if candidates else "clarify the requested concept"
    method = (
        candidates[0]["method"]
        if candidates
        else "Ask one targeted question about the intended behavior."
    )
    length_question = bool(re.search(r"\blength\b", question)) and not re.search(
        r"\b(?:error|fail|outside|bound|bounds|skip|last)\b|off-by-one", question
    )
    result_question = bool(
        re.search(
            r"\b(?:get|return|returns|returning|giving|result|output|fail|fails|wrong|hang|error|missing)\b|works.*\bnot\b",
            question,
        )
    )
    if length_question:
        candidates, basis, focus = [], "definition question", "array length"
        method = (
            "Count the array values, then compare length with the last valid index."
        )
    elif result_question and (
        supported := supported_confusion(request, case, evidence)
    ):
        candidates, basis = [CARDS[supported]], "execution evidence"
        focus, method = candidates[0]["title"], candidates[0]["method"]
    elif result_question and case["actual"] == -1 and case["target"] in case["values"]:
        candidates = [
            c for c in candidates if c["id"] not in {"early-return", "absent-target"}
        ]
        focus, method = (
            "result mismatch",
            "Compare the recorded comparisons with the target and the stated contract.",
        )
        basis = "execution evidence with no specific cause"
    elif (
        not candidates
        and request.history
        and re.search(r"\bit\b|still|differently|more help", question)
    ):
        prior = next(
            (t.content for t in reversed(request.history) if t.role == "user"), ""
        )
        candidates = ranked_cards(prior.lower().replace("−", "-"))
        if candidates:
            basis = "prior student question"
            focus, method = candidates[0]["title"], candidates[0]["method"]
    contract_cards = {"early-return", "index-vs-value", "duplicates", "absent-target"}
    clarify_intent = not request.include_problem and (
        result_question or any(c["id"] in contract_cards for c in candidates)
    )
    if not request.include_problem:
        candidates = [c for c in candidates if c["id"] not in contract_cards]
    if clarify_intent:
        candidates = []
        basis, focus, method = (
            "observations without a specification",
            "intended output is unspecified",
            "Describe the observed result and ask what output the student intends.",
        )
    observations = []
    if evidence["error"]:
        observations.append("Runner error: " + evidence["error"])
    else:
        observations.append(
            f"The runner returned {evidence['actual']} at line {evidence['return_line']}."
        )
    if evidence["compared_indices"]:
        observations.append(
            "Recorded array comparisons used indices "
            + str(evidence["compared_indices"])
            + "."
        )
    if request.include_problem:
        observations.append(
            f"This case expects {case['expected']}; actual output is {case['actual']}."
        )
    return {
        "question": request.question,
        "intent": "clarify intended output"
        if clarify_intent
        else "one clue"
        if request.mode == "hint"
        else "minimal diagnosis and correction"
        if request.mode == "debug"
        else "next-step prediction question"
        if request.mode == "predict"
        else "explain the selected code and observed step",
        "question_focus": focus,
        "selection_basis": basis,
        "candidate_confusions": candidates,
        "observations": observations,
        "evidence": evidence,
        "explanation_method": method,
        "limits": "These are teaching hypotheses. Keyword matches and program results do not diagnose a student's ability or establish mastery.",
    }
