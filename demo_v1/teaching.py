"""Question-specific teaching choices, with candidate misconceptions labeled."""

import json

from demo_v1.retrieval import ROOT

PACK = json.loads((ROOT / "teaching.json").read_text(encoding="utf-8"))


def choose(request, case):
    question = request.question.lower()
    scores = [
        (sum(len(term.split()) for term in card["question_terms"] if term in question), card)
        for card in PACK
    ]
    candidates = [
        card for score, card in sorted(scores, key=lambda item: -item[0]) if score
    ][:2]
    observations = []
    if case["error"] and "limit" in case["error"]:
        observations.append("The bounded runner reached its execution limit.")
        if not candidates:
            candidates = [next(c for c in PACK if c["id"] == "loop-progress")]
    elif case["actual"] == -1 and case["target"] in case["values"] and case["frames"]:
        frame = case["frames"][-1]
        observations.append(
            f"The runner returned -1 at line {frame['current_line']}, while the input contains the target."
        )
        observations.append(
            f"The final recorded index is {frame['variables'].get('i', 'unknown')}."
        )
        if not candidates:
            candidates = [next(c for c in PACK if c["id"] == "early-return")]
    else:
        observations.append(
            "No specific misconception has independent confirmation from this question."
        )
    return {
        "question": request.question,
        "intent": "one clue"
        if request.mode == "hint"
        else "minimal diagnosis and correction"
        if request.mode == "debug"
        else "next-step prediction question"
        if request.mode == "predict"
        else "explain the selected code and observed step",
        "candidate_confusions": candidates,
        "observations": observations,
        "explanation_method": candidates[0]["method"]
        if candidates
        else "Ask one targeted question about the intended behavior.",
        "limits": "These are teaching hypotheses. Keyword matches and program results do not diagnose a student's ability or establish mastery.",
    }
