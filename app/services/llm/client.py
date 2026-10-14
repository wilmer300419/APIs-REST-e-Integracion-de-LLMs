"""Clientes LLM (patrón Strategy / Adapter).

`LLMClient` define el contrato. Así el resto de la app no depende de un
proveedor concreto: cambiar de OpenAI a Gemini = añadir otra subclase.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.core.config import Settings
from app.core.exceptions import LLMUnavailableError

Message = dict[str, str]  # {"role": "system|user|assistant", "content": "..."}


class LLMClient(ABC):
    """Contrato común para cualquier proveedor de LLM."""

    @abstractmethod
    def generate(self, messages: list[Message]) -> str:
        """Envía la conversación al modelo y devuelve su respuesta en texto."""


class FakeLLMClient(LLMClient):
    """LLM simulado y determinista: permite pruebas y CI sin API key ni costo."""

    def generate(self, messages: list[Message]) -> str:
        last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        return f"[FAKE-LLM] Mensajes recibidos: {len(messages)}. Entrada: {last_user[:80]}"


class OpenAILLMClient(LLMClient):
    """Adaptador para OpenAI (GPT-4o)."""

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise LLMUnavailableError("OPENAI_API_KEY no está configurada")
        from openai import OpenAI  # import diferido: solo si se usa OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, messages: list[Message]) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model, messages=messages, temperature=0.2
            )
            return response.choices[0].message.content or ""
        except Exception as exc:  # errores de red, cuota, autenticación...
            raise LLMUnavailableError(f"Fallo al consultar el LLM: {exc}") from exc


def build_llm_client(settings: Settings) -> LLMClient:
    """Fábrica: elige la implementación según la configuración."""
    if settings.llm_provider == "openai":
        return OpenAILLMClient(settings.openai_api_key, settings.openai_model)
    return FakeLLMClient()
