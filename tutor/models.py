"""Versioned boundary between any visualizer and the tutor."""

import json
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    model_validator,
)

Text = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ChatTurn(StrictModel):
    role: Literal["user", "assistant"]
    content: Text


class ExecutionEvent(StrictModel):
    kind: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=500)
    line: int | None = Field(default=None, ge=1)
    indices: list[int] = Field(default_factory=list, max_length=20)
    details: dict[str, JsonValue] = Field(default_factory=dict, max_length=20)


class ExecutionContext(StrictModel):
    algorithm: str = Field(default="", max_length=120)
    language_version: str = Field(default="avp-repository-v1", max_length=80)
    code: str = Field(default="", max_length=16000)
    current_line: int | None = Field(default=None, ge=1)
    phase: Literal["before", "after", "unknown"] = "unknown"
    run_id: str = Field(default="", max_length=120)
    step: int | None = Field(default=None, ge=0)
    variables: dict[str, JsonValue] = Field(default_factory=dict, max_length=80)
    arrays: dict[str, list[JsonValue]] = Field(default_factory=dict, max_length=10)
    recent_events: list[ExecutionEvent] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def bounded_context(self) -> Self:
        if self.current_line is not None and (
            not self.code or self.current_line > len(self.code.splitlines())
        ):
            raise ValueError("current_line must refer to a line in code")
        if any(len(v) > 256 for v in self.arrays.values()):
            raise ValueError("each array is limited to 256 visible values")
        if len(json.dumps(self.model_dump(), ensure_ascii=False)) > 24000:
            raise ValueError("execution context exceeds 24000 characters")
        return self


class TutorRequest(StrictModel):
    feedback_consent: bool = False
    question: Text
    mode: Literal["explain", "hint", "predict", "debug"] = "explain"
    level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    context: ExecutionContext | None = None
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def history_budget(self) -> Self:
        if sum(len(t.content) for t in self.history) > 12000:
            raise ValueError(
                "history exceeds 12000 characters; send the most recent complete turns"
            )
        return self


class Source(StrictModel):
    id: str
    title: str
    path: str
    section: str
    text: str


class TutorResponse(StrictModel):
    interaction_id: str | None = None
    harness_version: str = ""
    skill: str = ""
    answer: str
    sources: list[Source] = Field(default_factory=list)
    context_status: Literal["provided", "partial", "missing"]
    warnings: list[str] = Field(default_factory=list)
    provider: str
    model: str
    latency_ms: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    prompt_version: str
    knowledge_version: str
    fallback_used: bool = False


class Diagnostic(StrictModel):
    line: int
    column: int
    message: str
    code: str = "syntax"
    severity: Literal["error", "warning"] = "error"


class ValidationResult(StrictModel):
    syntax_valid: bool
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    execution_verified: bool = False


class ValidateRequest(StrictModel):
    code: str = Field(min_length=1, max_length=16000)
