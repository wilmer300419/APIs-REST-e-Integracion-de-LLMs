"""Esquemas Pydantic (DTOs) para entrada y salida de la API de documentos.

Cada campo lleva `description` y cada modelo un `example`, de modo que la
documentación OpenAPI (/docs) muestre la estructura JSON exacta.
Se usa `example` (singular) porque es la forma válida en OpenAPI 3.0.
"""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """Campos comunes de creación y actualización."""

    title: str = Field(
        ..., min_length=3, max_length=120,
        description="Título único del documento (3 a 120 caracteres). No distingue mayúsculas.",
    )
    content: str = Field(
        ..., min_length=10,
        description="Texto completo del documento (mínimo 10 caracteres). "
                    "Es el texto que el RAG fragmenta y consulta.",
    )
    tags: list[str] = Field(
        default_factory=list, max_length=10,
        description="Etiquetas para clasificar el documento (máximo 10).",
    )


class DocumentCreate(DocumentBase):
    """Cuerpo de `POST /documents`."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Guía de matrícula",
        "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                   "en la oficina de admisiones antes del primer día de clases.",
        "tags": ["admisiones", "matrícula"],
    }})


class DocumentUpdate(DocumentBase):
    """Cuerpo de `PUT /documents/{id}` (reemplazo completo: se envían todos los campos)."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "title": "Guía de matrícula 2026",
        "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                   "en la oficina de admisiones. El plazo vence una semana antes de iniciar clases.",
        "tags": ["admisiones", "matrícula", "2026"],
    }})


class DocumentResponse(DocumentBase):
    """Representación pública de un documento."""

    model_config = ConfigDict(from_attributes=True, json_schema_extra={"example": {
        "id": 1,
        "title": "Guía de matrícula",
        "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                   "en la oficina de admisiones antes del primer día de clases.",
        "tags": ["admisiones", "matrícula"],
        "created_at": "2026-10-14T15:30:00.123456Z",
        "updated_at": "2026-10-14T15:30:00.123456Z",
    }})

    id: int = Field(..., description="Identificador único autogenerado.")
    created_at: datetime = Field(..., description="Fecha de creación (UTC, ISO 8601).")
    updated_at: datetime = Field(..., description="Fecha de la última modificación (UTC, ISO 8601).")


class ValidationIssue(BaseModel):
    """Un problema de validación en un campo concreto de la petición."""

    field: str = Field(..., description="Ruta del campo con error (p. ej. `title` o `tags.0`).")
    issue: str = Field(..., description="Descripción del problema.")


class ErrorResponse(BaseModel):
    """Formato uniforme de error: TODOS los errores de la API usan esta estructura."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "status": 404,
        "error": "not_found",
        "message": "Documento 999 no encontrado",
        "path": "/documents/999",
    }})

    status: int = Field(..., description="Código de estado HTTP (se repite en el cuerpo).")
    error: str = Field(
        ..., description="Código máquina del error: `not_found`, `conflict`, "
                         "`validation_error`, `llm_unavailable`, `http_error` o `internal_error`.",
    )
    message: str = Field(..., description="Mensaje legible para el usuario.")
    path: str = Field(..., description="Ruta de la petición que originó el error.")
    details: list[ValidationIssue] = Field(
        default_factory=list,
        description="Detalle por campo. Solo se incluye en errores 422 (validación).",
    )
