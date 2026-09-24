"""Scoped consistency checks of supplied events, never independent execution."""

import hashlib

from tutor.models import EvidenceReport, ExecutionContext


def same_json_value(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            same_json_value(a, b) for a, b in zip(left, right)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            same_json_value(left[k], right[k]) for k in left
        )
    return left == right


def inspect_evidence(context: ExecutionContext | None) -> EvidenceReport:
    report = EvidenceReport(
        limitations=["Checks compare supplied fields only; no AVP was executed."]
    )
    if context is None:
        report.limitations.append("No execution snapshot supplied.")
        return report
    report.code_version = context.code_version
    if context.code:
        report.code_sha256 = hashlib.sha256(context.code.encode()).hexdigest()
    if not context.recent_events or context.phase != "after":
        report.limitations.append(
            "No current after-phase event available for comparison."
        )
        return report
    event = context.recent_events[-1]
    if (
        event.line is None
        or event.line != context.current_line
        or event.kind not in {"shift", "copy"}
    ):
        report.limitations.append(
            "Latest event is not a current-line structured copy/shift."
        )
        return report
    details = event.details
    array_name = details.get("array_name")
    if array_name is None and len(context.arrays) == 1:
        array_name = next(iter(context.arrays))
    array = context.arrays.get(array_name) if isinstance(array_name, str) else None
    if array is None:
        report.limitations.append(
            "Array identity is missing or ambiguous; no array checks performed."
        )
    else:
        for name in ("source_index", "destination_index"):
            index = details.get(name)
            if type(index) is not int or "copied_value" not in details:
                report.limitations.append(f"Missing integer {name} or copied_value.")
                continue
            report.checks.append(f"{name} compared with copied_value in {array_name}.")
            if not 0 <= index < len(array):
                report.conflicts.append(f"{name} is outside the supplied array.")
            elif not same_json_value(array[index], details["copied_value"]):
                report.conflicts.append(f"{name} value disagrees with copied_value.")
    # saved_key is the documented event field for the snapshot variable named key.
    if "saved_key" in details and "key" in context.variables:
        report.checks.append("saved_key compared with snapshot variable key.")
        if not same_json_value(details["saved_key"], context.variables["key"]):
            report.conflicts.append("saved_key disagrees with snapshot variable key.")
    report.status = (
        "conflict"
        if report.conflicts
        else "consistent"
        if report.checks
        else "not_checked"
    )
    return report
