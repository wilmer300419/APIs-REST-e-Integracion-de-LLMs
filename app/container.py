"""Contenedor de dependencias: construye y conecta los objetos de la app."""
from __future__ import annotations

from app.core.config import Settings
from app.repositories.document_repository import InMemoryDocumentRepository
from app.services.document_service import DocumentService
from app.services.llm.client import build_llm_client
from app.services.rag_service import RagService, Retriever


class Container:
    """Agrupa las instancias compartidas (una por aplicación)."""

    def __init__(self, settings: Settings) -> None:
        self.repository = InMemoryDocumentRepository()
        self.document_service = DocumentService(self.repository)
        retriever = Retriever(settings.chunk_size, settings.chunk_overlap)
        self.rag_service = RagService(self.repository, build_llm_client(settings), retriever)
