"""Transparent teaching choices based on explicit input, not inferred ability."""

from tutor.models import EvidenceReport, TeachingDecision, TutorRequest

STRATEGIES = {
    "trace": "Explain using the supplied values and line. Separate before and after; do not invent unrecorded steps.",
    "analogy": "Use one short analogy, then map it back to actual code. State where the analogy stops applying.",
    "comparison": "Contrast the relevant operations or implementations. Identify differences explicitly; example code does not establish current-run behavior.",
    "invariant": "Explain what stays true, connect it to the supplied step, and distinguish the invariant from temporary array contents.",
    "worked-example": "Use a small illustrative example only when helpful. Label hypothetical values distinctly from current-run values. Do not call it an executed trace.",
    "guided-question": "Offer one concrete guiding question. Respect hint and predict mode; never reveal their target answer.",
}


def choose_teaching(
    request: TutorRequest, evidence: EvidenceReport
) -> TeachingDecision:
    strategy = request.strategy
    reasons = [f"Student selected {request.mode} mode."]
    if strategy == "auto":
        strategy = "guided-question" if request.mode in {"hint", "predict"} else "trace"
        reasons.append(
            "Default strategy for the requested mode; no learner-profile inference."
        )
    else:
        reasons.append(
            "Explicit student strategy preference honored, subject to mode and evidence constraints."
        )
    action = request.mode
    if evidence.conflicts:
        action = "clarify"
        reasons.append(
            "Supplied event and snapshot conflict; ask for a corrected snapshot before making current-step claims."
        )
    elif request.mode == "predict" and (
        request.context is None
        or not request.context.code
        or request.context.current_line is None
        or request.context.phase == "unknown"
        or not (request.context.variables or request.context.arrays)
    ):
        action = "clarify"
        reasons.append(
            "A grounded next-step prediction needs code, a current line, phase and state."
        )
    return TeachingDecision(action=action, strategy=strategy, reasons=reasons)
