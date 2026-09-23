# from typing import None

from typing import Annotated

from pydantic import AliasChoices, BaseModel, Field, StringConstraints

from tutor.models import ValidationResult

Query = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)
]


class GenerateRequest(BaseModel):
    query: Query = Field(validation_alias=AliasChoices("query", "message"))


class RetrievedFunction(BaseModel):
    score: float
    function_name: str
    parameters: list[str]
    code: str
    source_file: str = ""


class GenerateResponse(BaseModel):
    generated_code: str | None = None
    validation: ValidationResult | None = None
    retrieved_functions: list[RetrievedFunction] = []
    cached: bool = False


class HealthResponse(BaseModel):
    status: str = "ok"
    provider: str = ""
    model: str = ""
    knowledge_version: str = ""
    note: str = "Configuration status only; model reachability is checked on request."
    retriever_loaded: bool = False
    provider_configured: bool = False


class RetrieveRequest(BaseModel):
    query: Query
    k: int = Field(default=2, ge=1, le=10)


class RetrieveResponse(BaseModel):
    results: list[RetrievedFunction] = []
    cached: bool = False
