"""Punto de entrada de la aplicación FastAPI.

Ejecutar:  uvicorn app.main:app --reload
Swagger UI:  http://localhost:8000/docs   |   JSON OpenAPI: /openapi.json
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import ai, documents
from app.container import Container
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers

# Texto que Swagger UI muestra en la parte superior (en inglés, formato Markdown).
API_DESCRIPTION = """
REST API to manage a **knowledge base** of documents and query it with an **LLM** using **RAG**
(Retrieval-Augmented Generation).

## Recommended workflow
1. `POST /documents` to load one or more documents.
2. `POST /ai/ask` to ask questions about them (choose the prompt technique).
3. Check `sources` in the response to see which chunks support the answer.

## Prompt engineering techniques
| `technique` | Description |
|---|---|
| `zero_shot` | Direct instruction with context and question, no examples. |
| `few_shot` | Includes example Q&A pairs to fix the `Answer / Source` format. |
| `chain_of_thought` | Asks the model to reason step by step before the final answer. |

## Uniform error format
Every error returns the same JSON structure:
```json
{ "status": 404, "error": "not_found", "message": "Document 999 not found", "path": "/documents/999" }
```
`422` errors also include a `details` array with one entry per invalid field.

| Status | `error` | When it happens |
|---|---|---|
| 400-499 | `http_error` | Unknown route or method not allowed |
| 404 | `not_found` | The resource does not exist |
| 409 | `conflict` | Duplicate document title |
| 422 | `validation_error` | Body, path or query parameters break the validation rules |
| 500 | `internal_error` | Unexpected server error |
| 502 | `llm_unavailable` | The LLM provider failed or is not configured |

## LLM mode
With `LLM_PROVIDER=fake` (default) answers start with `[FAKE-LLM]` and no external API is called.
With `LLM_PROVIDER=openai` and `OPENAI_API_KEY` set, GPT-4o is used.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fábrica de la app: facilita crear instancias aisladas para las pruebas."""
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="Semester Project API",
        version="1.0.0",
        description=API_DESCRIPTION,
        contact={"name": "Semester Integrator Project - UMB"},
        openapi_tags=[
            {"name": "Documents",
             "description": "Knowledge base CRUD: create, list, retrieve, update and delete documents."},
            {"name": "AI (RAG)",
             "description": "Natural-language questions answered by an LLM using the stored documents as context."},
            {"name": "System", "description": "Monitoring utilities."},
        ],
    )
    # La práctica exige OpenAPI 3.0 (FastAPI emite 3.1 por defecto).
    app.openapi_version = "3.0.3"
    app.state.container = Container(settings)
    register_exception_handlers(app)
    app.include_router(documents.router)
    app.include_router(ai.router)

    @app.get("/health", tags=["System"], summary="Service health check",
             response_description="The service is up and running.",
             responses={200: {"content": {"application/json": {"example": {"status": "ok"}}}}})
    def health():
        """Returns `{"status": "ok"}` when the API is running. Useful for monitoring and CI."""
        return {"status": "ok"}

    return app


app = create_app()
