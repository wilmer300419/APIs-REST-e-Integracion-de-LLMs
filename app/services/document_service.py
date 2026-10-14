"""Lógica de negocio de documentos (casos de uso CRUD)."""
from __future__ import annotations

from app.core.exceptions import ConflictError, NotFoundError
from app.domain.document import Document
from app.repositories.document_repository import DocumentRepository
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentService:
    """Orquesta las reglas de negocio sobre el repositorio."""

    def __init__(self, repository: DocumentRepository) -> None:
        self._repo = repository

    def create(self, data: DocumentCreate) -> Document:
        """Crea un documento; el título debe ser único."""
        if self._repo.find_by_title(data.title):
            raise ConflictError(f"Ya existe un documento con el título '{data.title}'")
        return self._repo.add(data.title, data.content, data.tags)

    def get(self, document_id: int) -> Document:
        """Obtiene un documento o lanza NotFoundError."""
        doc = self._repo.get(document_id)
        if doc is None:
            raise NotFoundError(f"Documento {document_id} no encontrado")
        return doc

    def list(self, skip: int = 0, limit: int = 20) -> list[Document]:
        """Lista documentos con paginación simple."""
        return self._repo.list(skip, limit)

    def update(self, document_id: int, data: DocumentUpdate) -> Document:
        """Reemplaza los datos de un documento existente."""
        doc = self.get(document_id)
        other = self._repo.find_by_title(data.title)
        if other and other.id != document_id:
            raise ConflictError(f"Ya existe un documento con el título '{data.title}'")
        doc.update(data.title, data.content, data.tags)
        return doc

    def delete(self, document_id: int) -> None:
        """Elimina un documento o lanza NotFoundError."""
        if not self._repo.delete(document_id):
            raise NotFoundError(f"Documento {document_id} no encontrado")
