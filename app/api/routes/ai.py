"""Endpoint de IA: preguntas sobre los documentos mediante RAG + LLM (docs en inglés)."""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends

from app.api import docs
from app.api.dependencies import get_rag_service
from app.schemas.ai import AskRequest, AskResponse
from app.services.rag_service import RagService

router = APIRouter(prefix="/ai", tags=["AI (RAG)"], responses={**docs.INTERNAL_ERROR})


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask the knowledge base (RAG)",
    response_description="The LLM answer together with the document chunks that support it.",
    responses={
        200: {"content": {"application/json": {"examples": {
            "with_context": {"summary": "Related information was found", "value": {
                "answer": "Answer: The student ID card must be handed in at the admissions office "
                          "before the first day of classes.\nSource: Enrollment guide.",
                "technique": "few_shot",
                "sources": [{
                    "document_id": 1,
                    "title": "Enrollment guide",
                    "text": "To enroll, the student must pay the tuition fee and hand in the student ID card "
                            "at the admissions office before the first day of classes.",
                    "score": 1.342,
                }],
            }},
            "without_context": {"summary": "No document is related to the question", "value": {
                "answer": "No related information was found in the knowledge base.",
                "technique": "zero_shot",
                "sources": [],
            }},
        }}}},
        **docs.LLM_UNAVAILABLE,
        **docs.ASK_422,
    },
)
def ask(
    request: AskRequest = Body(..., openapi_examples={
        "zero_shot": {"summary": "Zero-shot: direct instruction, no examples", "value": {
            "question": "Where do I hand in my student ID card?", "technique": "zero_shot", "top_k": 3}},
        "few_shot": {"summary": "Few-shot: example Q&A pairs fix the 'Answer / Source' format", "value": {
            "question": "What time does the library close?", "technique": "few_shot", "top_k": 3}},
        "chain_of_thought": {"summary": "Chain-of-Thought: step-by-step reasoning", "value": {
            "question": "What do I need to enroll and until when?",
            "technique": "chain_of_thought", "top_k": 5}},
    }),
    service: RagService = Depends(get_rag_service),
):
    """Answers a question using **RAG** (Retrieval-Augmented Generation).

    **How it works**
    1. Stored documents are split into chunks of about 80 words.
    2. The `top_k` chunks most relevant to the question are retrieved.
    3. A prompt is built with the chosen `technique` and sent to the LLM.
    4. The answer is returned together with the `sources` that were used.

    If no chunk is relevant, the LLM is **not called**: a fixed notice is returned with an
    empty `sources` list (this avoids hallucinations and unnecessary cost).
    """
    return service.ask(request.question, request.technique, request.top_k)
