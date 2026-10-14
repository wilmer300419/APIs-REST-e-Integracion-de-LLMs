"""Endpoints CRUD de documentos (5 endpoints).

Cada ruta documenta en OpenAPI: parámetros, ejemplos del cuerpo de entrada,
respuesta exitosa y todos los errores posibles con su JSON de ejemplo.
"""
from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

from app.api import docs
from app.api.dependencies import get_document_service
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.services.document_service import DocumentService

# El 500 aplica a todas las rutas del router, por eso se declara una sola vez aquí.
router = APIRouter(prefix="/documents", tags=["Documentos"], responses={**docs.INTERNAL_ERROR})

# Parámetro de ruta reutilizado por GET, PUT y DELETE.
DocumentId = Path(..., ge=1, description="Identificador del documento (entero positivo).",
                  openapi_examples={"existente": {"summary": "Un documento existente", "value": 1}})


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un documento",
    response_description="Documento creado, con su `id` y fechas generadas por el servidor.",
    responses={**docs.CONFLICT, **docs.BODY_422},
)
def create_document(
    data: DocumentCreate = Body(..., openapi_examples={
        "completo": {
            "summary": "Documento con etiquetas",
            "value": {
                "title": "Guía de matrícula",
                "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                           "en la oficina de admisiones antes del primer día de clases.",
                "tags": ["admisiones", "matrícula"],
            },
        },
        "sin_etiquetas": {
            "summary": "Documento sin etiquetas (`tags` es opcional)",
            "value": {
                "title": "Horarios de biblioteca",
                "content": "La biblioteca abre de lunes a viernes de 7am a 9pm y los sábados de 8am a 1pm.",
            },
        },
    }),
    service: DocumentService = Depends(get_document_service),
):
    """Registra un nuevo documento en la base de conocimiento.

    **Reglas de negocio**
    - El `title` debe ser único (sin distinguir mayúsculas); si ya existe responde **409**.
    - `id`, `created_at` y `updated_at` los genera el servidor, no se envían.
    """
    return service.create(data)


@router.get(
    "",
    response_model=list[DocumentResponse],
    summary="Listar documentos",
    response_description="Arreglo JSON de documentos (vacío `[]` si no hay ninguno).",
    responses={**docs.LIST_422},
)
def list_documents(
    skip: int = Query(0, ge=0, description="Cantidad de documentos a omitir (paginación).",
                      openapi_examples={"primera_pagina": {"summary": "Desde el inicio", "value": 0}}),
    limit: int = Query(20, ge=1, le=100, description="Máximo de documentos a devolver (1 a 100).",
                       openapi_examples={"veinte": {"summary": "20 por página", "value": 20}}),
    service: DocumentService = Depends(get_document_service),
):
    """Devuelve los documentos en orden de creación, con paginación simple `skip`/`limit`."""
    return service.list(skip, limit)


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Obtener un documento por id",
    response_description="El documento solicitado.",
    responses={**docs.NOT_FOUND, **docs.PATH_422},
)
def get_document(document_id: int = DocumentId, service: DocumentService = Depends(get_document_service)):
    """Busca un documento por su identificador. Responde **404** si no existe."""
    return service.get(document_id)


@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Actualizar un documento",
    response_description="Documento con los datos nuevos y `updated_at` renovado.",
    responses={**docs.NOT_FOUND, **docs.CONFLICT, **docs.UPDATE_422},
)
def update_document(
    data: DocumentUpdate = Body(..., openapi_examples={
        "reemplazo_completo": {
            "summary": "Reemplazo de todos los campos",
            "value": {
                "title": "Guía de matrícula 2026",
                "content": "Para matricularse el estudiante debe pagar la matrícula y entregar el carné "
                           "en la oficina de admisiones. El plazo vence una semana antes de iniciar clases.",
                "tags": ["admisiones", "matrícula", "2026"],
            },
        },
    }),
    document_id: int = DocumentId,
    service: DocumentService = Depends(get_document_service),
):
    """Reemplaza por completo un documento existente (semántica PUT: se envían **todos** los campos).

    - **404** si el id no existe.
    - **409** si el nuevo `title` ya pertenece a *otro* documento.
    """
    return service.update(document_id, data)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un documento",
    response_description="Eliminado correctamente. La respuesta no tiene cuerpo.",
    responses={**docs.NOT_FOUND, **docs.PATH_422},
)
def delete_document(document_id: int = DocumentId, service: DocumentService = Depends(get_document_service)):
    """Elimina un documento de forma permanente. Responde **404** si no existe."""
    service.delete(document_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
