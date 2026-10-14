"""RAG básico: Retrieval (recuperación) + Augmented Generation (generación).

Flujo:
  1. Dividir cada documento en fragmentos (chunking) con solape.
  2. Puntuar los fragmentos según su similitud con la pregunta.
  3. Insertar los mejores fragmentos como CONTEXTO en el prompt.
  4. Pedir la respuesta al LLM.

Aquí el retriever usa coincidencia de palabras (sin dependencias pesadas).
Mejora sugerida para el proyecto final: reemplazarlo por embeddings + una
base vectorial (Chroma, pgvector, FAISS) implementando la misma interfaz.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from app.repositories.document_repository import DocumentRepository
from app.schemas.ai import AskResponse, SourceChunk
from app.services.llm.client import LLMClient
from app.services.llm.prompts import STRATEGIES

_STOPWORDS = {
    "el", "la", "los", "las", "de", "del", "y", "o", "a", "en", "un", "una", "que",
    "es", "se", "por", "para", "con", "al", "como", "cual", "cuales", "son", "su",
}


def _tokenize(text: str) -> list[str]:
    """Minúsculas, sin tildes y sin palabras vacías."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return [t for t in re.findall(r"\w+", normalized) if t not in _STOPWORDS]


@dataclass(frozen=True)
class Chunk:
    """Fragmento de un documento listo para ser recuperado."""

    document_id: int
    title: str
    text: str


class Retriever:
    """Divide documentos en fragmentos y recupera los más relevantes."""

    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._size = chunk_size
        self._step = max(1, chunk_size - chunk_overlap)

    def _chunk(self, document_id: int, title: str, content: str) -> list[Chunk]:
        words = content.split()
        return [
            Chunk(document_id, title, " ".join(words[i : i + self._size]))
            for i in range(0, max(len(words), 1), self._step)
        ]

    def search(self, query: str, documents, top_k: int) -> list[tuple[Chunk, float]]:
        """Devuelve hasta `top_k` fragmentos con puntaje > 0, de mayor a menor."""
        query_terms = set(_tokenize(query))
        scored: list[tuple[Chunk, float]] = []
        for doc in documents:
            for chunk in self._chunk(doc.id, doc.title, doc.content):
                # El título también aporta señal de relevancia.
                counts = Counter(_tokenize(f"{chunk.title} {chunk.text}"))
                hits = sum(counts[t] for t in query_terms)
                if hits:
                    scored.append((chunk, hits / math.sqrt(sum(counts.values()))))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


class RagService:
    """Caso de uso: responder preguntas usando documentos + LLM."""

    NO_CONTEXT_MESSAGE = "No encontré información relacionada en la base de conocimiento."

    def __init__(self, repository: DocumentRepository, llm: LLMClient, retriever: Retriever) -> None:
        self._repo = repository
        self._llm = llm
        self._retriever = retriever

    def ask(self, question: str, technique: str, top_k: int) -> AskResponse:
        results = self._retriever.search(question, self._repo.all(), top_k)

        # Sin contexto no se llama al LLM: evita alucinaciones y ahorra costo.
        if not results:
            return AskResponse(answer=self.NO_CONTEXT_MESSAGE, technique=technique, sources=[])

        context = "\n---\n".join(f"[{c.title}] {c.text}" for c, _ in results)
        messages = STRATEGIES[technique].build(question, context)
        answer = self._llm.generate(messages)

        sources = [
            SourceChunk(document_id=c.document_id, title=c.title, text=c.text, score=round(s, 3))
            for c, s in results
        ]
        return AskResponse(answer=answer, technique=technique, sources=sources)
