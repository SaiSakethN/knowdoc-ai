from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_format(cls, value):
        value = value.strip().lower()
        if "@" not in value or " " in value:
            raise ValueError("valid email required")
        return value


class CollectionInput(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class SearchInput(BaseModel):
    question: str = Field(min_length=3, max_length=2000)
    method: Literal["keyword", "dense", "hybrid", "hybrid_rerank"] = "hybrid"
    top_k: int = Field(default=6, ge=1, le=20)
    collection_id: str | None = Field(default=None, max_length=36)
    document_id: str | None = Field(default=None, max_length=36)
    version_ids: list[str] = Field(default_factory=list, max_length=20)


class AnswerInput(SearchInput):
    mode: Literal["evidence", "generate"] = "generate"


class GrantInput(BaseModel):
    email: str = Field(min_length=3, max_length=254)


class PassageOutput(BaseModel):
    id: str
    document_id: str
    title: str
    version_id: str
    version: str
    text: str
    quote_hash: str
    location: dict[str, Any]
    score: float
    source_url: str | None = None
    retrieved_at: str | None = None
    publication_date: str | None = None
    freshness: str
    rerank_score: float | None = None


class SearchOutput(BaseModel):
    passages: list[PassageOutput]
    method: str
    retrieval_ms: float


class CitationSpan(BaseModel):
    citation_id: str
    start: int
    end: int
    quote: str
    offset_basis: str


class ClaimOutput(BaseModel):
    text: str
    citation_ids: list[str]
    quote: str
    citation_spans: list[CitationSpan] = Field(default_factory=list)


class ConflictOutput(BaseModel):
    citation_ids: list[str]
    quotes: list[str]
    versions: list[str]
    reason: str


class AnswerOutput(BaseModel):
    answer_method: Literal["extractive", "local_model", "evidence"] = "evidence"
    status: Literal["answered", "evidence_only", "insufficient_evidence", "conflicting_evidence", "clarification_required"]
    answer: str
    claims: list[ClaimOutput]
    citations: list[PassageOutput]
    conflicts: list[ConflictOutput]
    mode: Literal["evidence", "generate"]
    usage: dict[str, Any] | None
    limitations: list[str]
    timings: dict[str, float]
