"""Punto de entrada de la aplicación FastAPI.

Ejecutar:  uvicorn app.main:app --reload
Docs OpenAPI:  http://localhost:8000/docs   |   JSON: /openapi.json
"""
from __future__ import annotations

from fastapi import FastAPI

from app.api.routes import ai, documents
from app.container import Container
from app.core.config import Settings
from app.core.exceptions import register_exception_handlers


API_DESCRIPTION = """
API REST para gestionar una **base de conocimiento** y consultarla con un **LLM** mediante **RAG**.

## Flujo de uso recomendado
1. `POST /documents` para cargar uno o más documentos.
2. `POST /ai/ask` para hacer preguntas sobre ellos (elige la técnica de prompt).
3. Revisa `sources` en la respuesta para ver qué fragmentos sustentan la respuesta.

## Formato uniforme de errores
Todos los errores devuelven el mismo JSON:
```json
{ "status": 404, "error": "not_found", "message": "Documento 999 no encontrado", "path": "/documents/999" }
```
En errores **422** se añade `details` con una entrada por campo inválido.

| Código | `error` | Cuándo ocurre |
|---|---|---|
| 400-499 | `http_error` | Ruta inexistente o método no permitido |
| 404 | `not_found` | El recurso no existe |
| 409 | `conflict` | Título de documento duplicado |
| 422 | `validation_error` | El JSON, parámetro de ruta o query no cumple las reglas |
| 500 | `internal_error` | Error inesperado del servidor |
| 502 | `llm_unavailable` | El proveedor del LLM falló o no está configurado |

## Modo del LLM
Con `LLM_PROVIDER=fake` (por defecto) las respuestas empiezan con `[FAKE-LLM]` y no consumen API.
Con `LLM_PROVIDER=openai` y `OPENAI_API_KEY` se usa GPT-4o.
"""


def create_app(settings: Settings | None = None) -> FastAPI:
    """Fábrica de la app: facilita crear instancias aisladas para las pruebas."""
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="API Proyecto Semestral",
        version="1.0.0",
        description=API_DESCRIPTION,
        contact={"name": "Proyecto Semestral Integrador - UMB"},
        openapi_tags=[
            {"name": "Documentos",
             "description": "CRUD de la base de conocimiento: crear, listar, consultar, actualizar y eliminar."},
            {"name": "IA (RAG)",
             "description": "Preguntas en lenguaje natural respondidas por un LLM con contexto de los documentos."},
            {"name": "Sistema", "description": "Utilidades de monitoreo."},
        ],
    )
    # La práctica exige OpenAPI 3.0 (FastAPI emite 3.1 por defecto).
    app.openapi_version = "3.0.3"
    app.state.container = Container(settings)
    register_exception_handlers(app)
    app.include_router(documents.router)
    app.include_router(ai.router)

    @app.get("/health", tags=["Sistema"], summary="Estado del servicio")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
