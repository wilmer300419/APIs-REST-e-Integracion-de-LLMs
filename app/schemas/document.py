"""Esquemas Pydantic (DTOs) de la API de documentos.

Los textos visibles en Swagger UI (descripciones y ejemplos) están en inglés.
Se usa `example` (singular) porque es la forma válida en OpenAPI 3.0.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """Fields shared by the create and update payloads."""

    title: str = Field(
        ..., min_length=3, max_length=120,
        description="Unique document title (3 to 120 characters). Case-insensitive.",
    )
    content: str = Field(
        ..., min_length=10,
        description="Full text of the document (at least 10 characters). "
                    "This is the text the RAG pipeline splits into chunks and searches.",
    )
    tags: list[str] = Field(
        default_factory=list, max_length=10,
        description="Optional labels used to classify the document (maximum 10).",
    )


class DocumentCreate(DocumentBase):
    """Request body of `POST /documents`."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Enrollment guide",
        "content": "To enroll, the student must pay the tuition fee and hand in the student ID card "
                   "at the admissions office before the first day of classes.",
        "tags": ["admissions", "enrollment"],
    }})


class DocumentUpdate(DocumentBase):
    """Request body of `PUT /documents/{id}` (full replacement: every field must be sent)."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Enrollment guide 2026",
        "content": "To enroll, the student must pay the tuition fee and hand in the student ID card "
                   "at the admissions office. The deadline is one week before classes start.",
        "tags": ["admissions", "enrollment", "2026"],
    }})


class DocumentResponse(DocumentBase):
    """Public representation of a document."""

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {
        "id": 1,
        "title": "Enrollment guide",
        "content": "To enroll, the student must pay the tuition fee and hand in the student ID card "
                   "at the admissions office before the first day of classes.",
        "tags": ["admissions", "enrollment"],
        "created_at": "2026-10-14T15:30:00.123456Z",
        "updated_at": "2026-10-14T15:30:00.123456Z",
    }})

    id: int = Field(..., description="Auto-generated unique identifier.")
    created_at: datetime = Field(..., description="Creation timestamp (UTC, ISO 8601).")
    updated_at: datetime = Field(..., description="Last modification timestamp (UTC, ISO 8601).")


class ValidationIssue(BaseModel):
    """A validation problem found in a specific field of the request."""

    field: str = Field(..., description="Path of the invalid field (e.g. `title` or `tags.0`).")
    issue: str = Field(..., description="Description of the problem.")


class ErrorResponse(BaseModel):
    """Uniform error format: EVERY error returned by this API uses this structure."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "status": 404,
        "error": "not_found",
        "message": "Document 999 not found",
        "path": "/documents/999",
    }})

    status: int = Field(..., description="HTTP status code (repeated in the body).")
    error: str = Field(
        ..., description="Machine-readable error code: `not_found`, `conflict`, "
                         "`validation_error`, `llm_unavailable`, `http_error` or `internal_error`.",
    )
    message: str = Field(..., description="Human-readable message.")
    path: str = Field(..., description="Path of the request that caused the error.")
    details: list[ValidationIssue] = Field(
        default_factory=list,
        description="Per-field details. Only present in 422 (validation) errors.",
    )
