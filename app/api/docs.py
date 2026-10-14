"""Piezas reutilizables para documentar respuestas en OpenAPI (en inglés).

Centraliza los ejemplos de error para que todas las rutas muestren
exactamente el mismo JSON que la API devuelve en la práctica.
"""
from __future__ import annotations

from app.schemas.document import ErrorResponse


def _error(description: str, examples: dict[str, dict]) -> dict:
    """Arma la definición de una respuesta de error con uno o varios ejemplos."""
    return {
        "model": ErrorResponse,
        "description": description,
        "content": {"application/json": {"examples": examples}},
    }


def _example(summary: str, status: int, error: str, message: str, path: str, details=None) -> dict:
    value = {"status": status, "error": error, "message": message, "path": path}
    if details:
        value["details"] = details
    return {"summary": summary, "value": value}


_INT_ISSUE = "Input should be a valid integer, unable to parse string as an integer"

NOT_FOUND = {404: _error("Document not found", {
    "not_found": _example("The id does not exist", 404, "not_found",
                          "Document 999 not found", "/documents/999"),
})}

CONFLICT = {409: _error("A document with that title already exists", {
    "duplicate_title": _example("Repeated title", 409, "conflict",
                                "A document with the title 'Enrollment guide' already exists", "/documents"),
})}

INTERNAL_ERROR = {500: _error("Unexpected internal error (details are only written to the server log)", {
    "internal_error": _example("Unhandled failure", 500, "internal_error",
                               "Internal server error", "/documents"),
})}

LLM_UNAVAILABLE = {502: _error("The LLM provider failed or is not configured", {
    "llm_failure": _example("Failed to query the LLM", 502, "llm_unavailable",
                            "Failed to query the LLM: Incorrect API key provided", "/ai/ask"),
})}


def validation_error(examples: dict[str, dict]) -> dict:
    """Respuesta 422 con ejemplos propios de cada endpoint."""
    return {422: _error("Invalid input data", examples)}


BODY_422 = validation_error({
    "invalid_fields": _example(
        "Title and content too short", 422, "validation_error", "Invalid input data", "/documents",
        [{"field": "title", "issue": "String should have at least 3 characters"},
         {"field": "content", "issue": "String should have at least 10 characters"}]),
    "missing_field": _example(
        "A required field is missing", 422, "validation_error", "Invalid input data", "/documents",
        [{"field": "content", "issue": "Field required"}]),
})

LIST_422 = validation_error({
    "invalid_pagination": _example(
        "Pagination parameters out of range", 422, "validation_error", "Invalid input data", "/documents",
        [{"field": "limit", "issue": "Input should be less than or equal to 100"}]),
})

PATH_422 = validation_error({
    "invalid_id": _example(
        "The id is not a positive integer", 422, "validation_error", "Invalid input data",
        "/documents/abc", [{"field": "document_id", "issue": _INT_ISSUE}]),
})

UPDATE_422 = validation_error({
    "invalid_fields": _example(
        "Invalid request body", 422, "validation_error", "Invalid input data", "/documents/1",
        [{"field": "title", "issue": "String should have at least 3 characters"}]),
    "invalid_id": _example(
        "The id is not a positive integer", 422, "validation_error", "Invalid input data",
        "/documents/abc", [{"field": "document_id", "issue": _INT_ISSUE}]),
})

ASK_422 = validation_error({
    "invalid_technique": _example(
        "Unsupported prompt technique", 422, "validation_error", "Invalid input data", "/ai/ask",
        [{"field": "technique", "issue": "Input should be 'zero_shot', 'few_shot' or 'chain_of_thought'"}]),
    "short_question": _example(
        "Question too short", 422, "validation_error", "Invalid input data", "/ai/ask",
        [{"field": "question", "issue": "String should have at least 5 characters"}]),
})
