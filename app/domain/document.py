"""Entidad de dominio: Document.

Representa un documento de la base de conocimiento del proyecto.
Es una clase simple, independiente de FastAPI y de la base de datos.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Document:
    """Documento con título, contenido y etiquetas."""

    id: int
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def update(self, title: str, content: str, tags: list[str]) -> None:
        """Modifica los datos del documento y refresca la fecha de actualización."""
        self.title = title
        self.content = content
        self.tags = tags
        self.updated_at = _utcnow()
