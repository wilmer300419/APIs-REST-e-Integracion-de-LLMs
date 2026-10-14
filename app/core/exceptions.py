"""Excepciones de dominio y su traducción a respuestas HTTP.

El dominio lanza excepciones propias (sin saber nada de HTTP) y esta capa
las convierte en respuestas JSON con un formato de error uniforme.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class DomainError(Exception):
    """Clase base de los errores de negocio."""

    status_code = 400
    error = "bad_request"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """El recurso solicitado no existe (HTTP 404)."""

    status_code = 404
    error = "not_found"


class ConflictError(DomainError):
    """El recurso ya existe o viola una regla de unicidad (HTTP 409)."""

    status_code = 409
    error = "conflict"


class LLMUnavailableError(DomainError):
    """El proveedor del LLM falló o no está configurado (HTTP 502)."""

    status_code = 502
    error = "llm_unavailable"


def _body(status: int, error: str, message: str, request: Request, details=None) -> JSONResponse:
    """Construye el cuerpo estándar de error."""
    payload = {"status": status, "error": error, "message": message, "path": request.url.path}
    if details is not None:
        payload["details"] = details
    return JSONResponse(status_code=status, content=payload)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de errores en la aplicación."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError):
        return _body(exc.status_code, exc.error, exc.message, request)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        # 422: el cliente envió datos que no cumplen el esquema.
        # loc[0] indica dónde falló (body/query/path); se omite para dejar solo el nombre del campo.
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "issue": e["msg"]}
            for e in exc.errors()
        ]
        return _body(422, "validation_error", "Invalid input data", request, details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        return _body(exc.status_code, "http_error", str(exc.detail), request)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception):
        # 500: se registra el detalle en el log pero no se expone al cliente.
        logger.exception("Error no controlado")
        return _body(500, "internal_error", "Internal server error", request)
