"""Shared data models for DFARS context records."""

from pydantic import BaseModel, Field


class PageText(BaseModel):
    """Text extracted from a single PDF page."""

    page_number: int = Field(ge=1)
    text: str


class SectionRecord(BaseModel):
    """Structured DFARS section with source text and retrieval metadata."""

    section_id: str
    title: str
    part: str | None = None
    subpart: str | None = None
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)
    original_text: str
    summary: str = ""
    key_topics: list[str] = Field(default_factory=list)
    applies_when: list[str] = Field(default_factory=list)
    required_actions: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    cross_references: list[str] = Field(default_factory=list)
    contracting_officer_notes: list[str] = Field(default_factory=list)


class RetrievedSection(BaseModel):
    """Retrieved section plus score used for context selection."""

    section: SectionRecord
    score: float
    retrieval_method: str
