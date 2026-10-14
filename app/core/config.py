"""Configuración centralizada de la aplicación.

Todos los valores sensibles (API keys) se leen desde variables de entorno,
nunca se escriben en el código ni se suben al repositorio.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Configuración inmutable de la aplicación."""

    llm_provider: str = "fake"          # "fake" (pruebas/CI) | "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    chunk_size: int = 80                # palabras por fragmento (RAG)
    chunk_overlap: int = 20             # palabras compartidas entre fragmentos

    @classmethod
    def from_env(cls) -> "Settings":
        """Construye la configuración leyendo variables de entorno."""
        return cls(
            llm_provider=os.getenv("LLM_PROVIDER", "fake").lower(),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        )
