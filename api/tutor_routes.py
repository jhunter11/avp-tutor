import asyncio

from fastapi import APIRouter, HTTPException, Request

from api.dependencies import limiter
from tutor import service
from tutor.demo import build_trace
from tutor.models import (
    ExecutionContext,
    TutorRequest,
    TutorResponse,
    ValidateRequest,
    ValidationResult,
)
from tutor.validation import validate_avp

router = APIRouter(prefix="/api")


@router.post("/tutor", response_model=TutorResponse)
@limiter.limit("20/minute")
async def tutor(body: TutorRequest, request: Request):
    try:
        return await asyncio.to_thread(service.answer_question, body)
    except Exception:
        # SDK exception messages can contain endpoint details or credentials.
        raise HTTPException(
            503,
            "The tutor model is unavailable or busy. Check the server's model configuration and try again.",
        ) from None


@router.post("/validate", response_model=ValidationResult)
@limiter.limit("30/minute")
async def validate(body: ValidateRequest, request: Request):
    return await asyncio.to_thread(validate_avp, body.code)


@router.get("/demo/insertion-sort")
async def demo(values: str = "2,7,9,4"):
    try:
        if len(values) > 200:
            raise ValueError("Input too long")
        numbers = (
            [] if not values.strip() else [int(v.strip()) for v in values.split(",")]
        )
        return {
            "algorithm": "insertion_sort",
            "frames": [f.model_dump() for f in build_trace(numbers)],
        }
    except ValueError:
        raise HTTPException(
            422, "Use up to 24 comma-separated integers between -999 and 999."
        ) from None


@router.post("/context/validate", response_model=ExecutionContext)
async def validate_context(body: ExecutionContext):
    return body
