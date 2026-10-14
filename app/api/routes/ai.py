"""Endpoint de IA: preguntas sobre los documentos mediante RAG + LLM."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.api import docs
from app.api.dependencies import get_rag_service
from app.schemas.ai import AskRequest, AskResponse
from app.services.rag_service import RagService

router = APIRouter(prefix="/ai", tags=["IA (RAG)"], responses={**docs.INTERNAL_ERROR})

_NO_CONTEXT_EXAMPLE = {
    "answer": "No encontré información relacionada en la base de conocimiento.",
    "technique": "zero_shot",
    "sources": [],
}


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Preguntar a la base de conocimiento (RAG)",
    response_description="Respuesta del LLM junto con los fragmentos que la sustentan.",
    responses={
        200: {"content": {"application/json": {"examples": {
            "con_contexto": {"summary": "Se encontró información", "value": {
                "answer": "Respuesta: El carné se entrega en la oficina de admisiones, "
                          "antes del primer día de clases.\nFuente: Guía de matrícula.",
                "technique": "few_shot",
                "sources": [{
                    "document_id": 1,
                    "title": "Guía de matrícula",
                    "text": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                            "en la oficina de admisiones antes del primer día de clases.",
                    "score": 1.342,
                }],
            }},
            "sin_contexto": {"summary": "Ningún documento se relaciona con la pregunta",
                             "value": _NO_CONTEXT_EXAMPLE},
        }}}},
        **docs.LLM_UNAVAILABLE,
        **docs.ASK_422,
    },
)
def ask(
    request: AskRequest = Body(..., openapi_examples={
        "zero_shot": {"summary": "Zero-shot: instrucción directa, sin ejemplos", "value": {
            "question": "¿Dónde debo entregar el carné?", "technique": "zero_shot", "top_k": 3}},
        "few_shot": {"summary": "Few-shot: con ejemplos de formato 'Respuesta / Fuente'", "value": {
            "question": "¿Hasta qué hora abre la biblioteca?", "technique": "few_shot", "top_k": 3}},
        "chain_of_thought": {"summary": "Chain-of-Thought: razonamiento paso a paso", "value": {
            "question": "¿Qué necesito para matricularme y hasta cuándo?",
            "technique": "chain_of_thought", "top_k": 5}},
    }),
    service: RagService = Depends(get_rag_service),
):
    """Responde una pregunta usando **RAG** (Retrieval-Augmented Generation).

    **Flujo**
    1. Los documentos guardados se dividen en fragmentos de ~80 palabras.
    2. Se recuperan los `top_k` fragmentos más relevantes para la pregunta.
    3. Se arma un prompt con la técnica elegida (`technique`) y se envía al LLM.
    4. Se devuelve la respuesta junto con las `sources` usadas.

    Si ningún fragmento es relevante, **no se llama al LLM**: se responde con un aviso
    y `sources` vacío (evita alucinaciones y gasto innecesario).
    """
    return service.ask(request.question, request.technique, request.top_k)
