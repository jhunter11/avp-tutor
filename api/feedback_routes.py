from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import Field

from api.dependencies import limiter
from harness.feedback import feedback_enabled, get_store
from tutor.models import StrictModel

router = APIRouter(prefix="/api")


class FeedbackRequest(StrictModel):
    interaction_id: str = Field(min_length=20, max_length=100)
    rating: Literal[
        "helpful", "incorrect", "too_much_answer", "too_vague", "missing_context"
    ]
    comment: str = Field(default="", max_length=1000)


class UsageRequest(StrictModel):
    consent: Literal[True]
    event: Literal[
        "offered",
        "opened",
        "dismissed",
        "asked",
        "prediction_correct",
        "prediction_incorrect",
    ]
    algorithm: str = Field(default="", max_length=120)


def require_store():
    if not feedback_enabled():
        raise HTTPException(403, "Feedback capture is disabled on this server.")
    return get_store()


@router.post("/feedback")
@limiter.limit("30/minute")
def feedback(body: FeedbackRequest, request: Request):
    try:
        require_store().add_feedback(body.interaction_id, body.rating, body.comment)
    except KeyError:
        raise HTTPException(404, "Unknown or expired interaction.") from None
    return {"saved": True}


@router.delete("/feedback/{interaction_id}", status_code=204)
@limiter.limit("30/minute")
def delete_feedback(interaction_id: str, request: Request):
    if not require_store().delete(interaction_id):
        raise HTTPException(404, "Unknown or expired interaction.")
    return Response(status_code=204)


@router.post("/usage")
@limiter.limit("60/minute")
def usage(body: UsageRequest, request: Request):
    require_store().record_usage(body.event, body.algorithm)
    return {"saved": True, "quality_label": False}
