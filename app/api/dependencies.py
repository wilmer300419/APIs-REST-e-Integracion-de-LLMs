"""Dependencias inyectables de FastAPI (Depends)."""
from __future__ import annotations

from fastapi import Request

from app.services.document_service import DocumentService
from app.services.rag_service import RagService


def get_document_service(request: Request) -> DocumentService:
    return request.app.state.container.document_service


def get_rag_service(request: Request) -> RagService:
    return request.app.state.container.rag_service
