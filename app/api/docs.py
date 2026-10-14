"""Piezas reutilizables para documentar respuestas en OpenAPI.

Centraliza los ejemplos de error para que todas las rutas muestren
exactamente el mismo formato JSON que devuelve la API en la práctica.
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


NOT_FOUND = {404: _error("Documento no encontrado", {
    "no_existe": _example("El id no existe", 404, "not_found",
                          "Documento 999 no encontrado", "/documents/999"),
})}

CONFLICT = {409: _error("Ya existe un documento con ese título", {
    "titulo_duplicado": _example("Título repetido", 409, "conflict",
                                 "Ya existe un documento con el título 'Guía de matrícula'", "/documents"),
})}

INTERNAL_ERROR = {500: _error("Error interno inesperado (el detalle solo queda en el log)", {
    "error_interno": _example("Fallo no controlado", 500, "internal_error",
                              "Error interno del servidor", "/documents"),
})}

LLM_UNAVAILABLE = {502: _error("El proveedor del LLM falló o no está configurado", {
    "sin_api_key": _example("Fallo al consultar el LLM", 502, "llm_unavailable",
                            "Fallo al consultar el LLM: Incorrect API key provided", "/ai/ask"),
})}


def validation_error(examples: dict[str, dict]) -> dict:
    """Respuesta 422 con ejemplos propios de cada endpoint."""
    return {422: _error("Datos de entrada inválidos", examples)}


# Ejemplos de 422 por tipo de endpoint -------------------------------------------------
BODY_422 = validation_error({
    "campos_invalidos": _example(
        "Título y contenido demasiado cortos", 422, "validation_error", "Datos de entrada inválidos",
        "/documents",
        [{"field": "title", "issue": "String should have at least 3 characters"},
         {"field": "content", "issue": "String should have at least 10 characters"}]),
    "campo_faltante": _example(
        "Falta un campo obligatorio", 422, "validation_error", "Datos de entrada inválidos",
        "/documents", [{"field": "content", "issue": "Field required"}]),
})

LIST_422 = validation_error({
    "paginacion_invalida": _example(
        "Parámetros de paginación fuera de rango", 422, "validation_error", "Datos de entrada inválidos",
        "/documents", [{"field": "limit", "issue": "Input should be less than or equal to 100"}]),
})

PATH_422 = validation_error({
    "id_invalido": _example(
        "El id no es un entero positivo", 422, "validation_error", "Datos de entrada inválidos",
        "/documents/abc", [{"field": "document_id",
                            "issue": "Input should be a valid integer, unable to parse string as an integer"}]),
})

UPDATE_422 = validation_error({
    "campos_invalidos": _example(
        "Cuerpo inválido", 422, "validation_error", "Datos de entrada inválidos",
        "/documents/1", [{"field": "title", "issue": "String should have at least 3 characters"}]),
    "id_invalido": _example(
        "El id no es un entero positivo", 422, "validation_error", "Datos de entrada inválidos",
        "/documents/abc", [{"field": "document_id",
                            "issue": "Input should be a valid integer, unable to parse string as an integer"}]),
})

ASK_422 = validation_error({
    "tecnica_invalida": _example(
        "Técnica de prompt no soportada", 422, "validation_error", "Datos de entrada inválidos",
        "/ai/ask", [{"field": "technique",
                     "issue": "Input should be 'zero_shot', 'few_shot' or 'chain_of_thought'"}]),
    "pregunta_corta": _example(
        "Pregunta demasiado corta", 422, "validation_error", "Datos de entrada inválidos",
        "/ai/ask", [{"field": "question", "issue": "String should have at least 5 characters"}]),
})
