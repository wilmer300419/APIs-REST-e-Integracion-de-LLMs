"""Capa de persistencia (patrón Repository).

`DocumentRepository` es una abstracción: el servicio depende de ella y no
de una base de datos concreta (principio de inversión de dependencias).
Para el proyecto final basta crear otra implementación (p. ej. SQLAlchemy)
sin tocar el servicio ni los endpoints.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from threading import Lock

from app.domain.document import Document


class DocumentRepository(ABC):
    """Contrato de acceso a datos para documentos."""

    @abstractmethod
    def add(self, title: str, content: str, tags: list[str]) -> Document: ...

    @abstractmethod
    def get(self, document_id: int) -> Document | None: ...

    @abstractmethod
    def find_by_title(self, title: str) -> Document | None: ...

    @abstractmethod
    def list(self, skip: int, limit: int) -> list[Document]: ...

    @abstractmethod
    def all(self) -> list[Document]: ...

    @abstractmethod
    def delete(self, document_id: int) -> bool: ...


class InMemoryDocumentRepository(DocumentRepository):
    """Implementación en memoria (segura entre hilos) para desarrollo y pruebas."""

    def __init__(self) -> None:
        self._items: dict[int, Document] = {}
        self._next_id = 1
        self._lock = Lock()

    def add(self, title: str, content: str, tags: list[str]) -> Document:
        with self._lock:
            doc = Document(id=self._next_id, title=title, content=content, tags=tags)
            self._items[doc.id] = doc
            self._next_id += 1
            return doc

    def get(self, document_id: int) -> Document | None:
        return self._items.get(document_id)

    def find_by_title(self, title: str) -> Document | None:
        return next((d for d in self._items.values() if d.title.lower() == title.lower()), None)

    def list(self, skip: int, limit: int) -> list[Document]:
        return list(self._items.values())[skip : skip + limit]

    def all(self) -> list[Document]:
        return list(self._items.values())

    def delete(self, document_id: int) -> bool:
        with self._lock:
            return self._items.pop(document_id, None) is not None
