"""Esquemas Pydantic para los endpoints de IA (RAG + prompt engineering)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Technique = Literal["zero_shot", "few_shot", "chain_of_thought"]


class AskRequest(BaseModel):
    """Pregunta del usuario sobre la base de conocimiento."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "question": "¿Dónde debo entregar el carné?",
        "technique": "zero_shot",
        "top_k": 3,
    }})

    question: str = Field(
        ..., min_length=5, max_length=500,
        description="Pregunta en lenguaje natural (5 a 500 caracteres).",
    )
    technique: Technique = Field(
        "zero_shot",
        description="Técnica de prompt engineering: `zero_shot` (sin ejemplos), "
                    "`few_shot` (con ejemplos de formato) o `chain_of_thought` (razonamiento paso a paso).",
    )
    top_k: int = Field(
        3, ge=1, le=10,
        description="Cantidad máxima de fragmentos de documentos a usar como contexto (1 a 10).",
    )


class SourceChunk(BaseModel):
    """Fragmento recuperado que sirvió de contexto."""

    document_id: int = Field(..., description="Id del documento del que proviene el fragmento.")
    title: str = Field(..., description="Título del documento de origen.")
    text: str = Field(..., description="Texto del fragmento (aprox. 80 palabras).")
    score: float = Field(..., description="Relevancia respecto a la pregunta; mayor = más relevante.")


class AskResponse(BaseModel):
    """Respuesta generada junto con sus fuentes (trazabilidad del RAG)."""

    model_config = ConfigDict(json_schema_extra={"example": {
        "answer": "Respuesta: El carné se entrega en la oficina de admisiones, antes del primer día de clases.\n"
                  "Fuente: Guía de matrícula.",
        "technique": "few_shot",
        "sources": [{
            "document_id": 1,
            "title": "Guía de matrícula",
            "text": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                    "en la oficina de admisiones antes del primer día de clases.",
            "score": 1.342,
        }],
    }})

    answer: str = Field(
        ..., description="Texto generado por el LLM. Si no hay contexto relevante, "
                         "es un aviso fijo y el LLM no se invoca.",
    )
    technique: Technique = Field(..., description="Técnica de prompt que se utilizó.")
    sources: list[SourceChunk] = Field(
        ..., description="Fragmentos usados como contexto, ordenados por relevancia. "
                         "Lista vacía si no se encontró información relacionada.",
    )
