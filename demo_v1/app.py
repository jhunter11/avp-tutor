"""Loopback-only document demo; separate from the product and test frontends."""

import asyncio
import os
import secrets
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

ROOT = Path(__file__).resolve().parent
env_path = os.environ.get("AVP_DEMO_ENV") or os.environ.get("AVP_GEMINI_ENV")
load_dotenv(Path(env_path) if env_path else ROOT.parent / ".env")

from api.middleware import BodyLimitMiddleware
from demo_v1.memory import LearnerMemory
from demo_v1.service import CONFIG, AskRequest, RunRequest, answer, run_code
from harness.config import harness_version
from providers import get_provider_name, is_provider_configured, provider_model
from tutor.models import StrictModel

app = FastAPI(title="AVP Tutor V1 document demo", docs_url=None, redoc_url=None)
app.add_middleware(BodyLimitMiddleware, max_bytes=65536)
TOKEN = secrets.token_urlsafe(32)
SLOT = asyncio.Semaphore(1)


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.url.hostname not in {"127.0.0.1", "localhost", "testserver"}:
        return JSONResponse(
            {"detail": "Open the demo through localhost."}, status_code=403
        )
    if request.method not in {"GET", "HEAD"}:
        origin = request.headers.get("origin")
        if origin and (
            urlparse(origin).scheme != request.url.scheme
            or urlparse(origin).netloc != request.url.netloc
        ):
            return JSONResponse(
                {"detail": "Open the demo through the same local address."},
                status_code=403,
            )
        if not secrets.compare_digest(request.headers.get("x-demo-token", ""), TOKEN):
            return JSONResponse(
                {"detail": "The demo session expired. Reload this page."},
                status_code=403,
            )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
    )
    return response


@app.get("/demo/api/status")
def status():
    from demo_v1.exercise import PROBLEM

    return {
        "provider": get_provider_name(),
        "model": provider_model(),
        "configured": is_provider_configured(),
        "token": TOKEN,
        "harness_version": harness_version(CONFIG),
        "problem": PROBLEM,
    }


@app.post("/demo/api/run")
async def run(request: RunRequest):
    try:
        return await asyncio.to_thread(run_code, request)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None


@app.post("/demo/api/ask")
async def ask(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(422, "Write a question first.")
    if not is_provider_configured():
        raise HTTPException(
            503,
            "The tutor provider is not configured. Start the demo with the path to your local key file.",
        )
    if SLOT.locked():
        raise HTTPException(
            429, "The tutor is answering another question. Try again shortly."
        )
    async with SLOT:
        try:
            return await asyncio.to_thread(answer, request)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        except Exception:
            raise HTTPException(
                503,
                "The provider did not return an answer. Check the key, model access, or quota, then retry.",
            ) from None


class NoteRequest(StrictModel):
    text: str = Field(min_length=1, max_length=400)


@app.get("/demo/api/notes")
def notes():
    return LearnerMemory().notes()


@app.post("/demo/api/notes")
def add_note(request: NoteRequest):
    try:
        LearnerMemory().add(request.text)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from None
    return {"saved": True}


@app.delete("/demo/api/notes/{note_id}")
def delete_note(note_id: str):
    if not LearnerMemory().delete(note_id):
        raise HTTPException(404, "This note no longer exists.")
    return {"deleted": True}


app.mount("/", StaticFiles(directory=str(ROOT / "web"), html=True), name="document")
