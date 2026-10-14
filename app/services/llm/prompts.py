"""Técnicas de prompt engineering (patrón Strategy).

Cada técnica es una clase que sabe construir los mensajes para el LLM a
partir de la pregunta y del contexto recuperado por RAG.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.llm.client import Message

SYSTEM_BASE = (
    "Eres un asistente académico. Responde SOLO con base en el CONTEXTO dado. "
    "Si el contexto no contiene la respuesta, di que no tienes esa información. "
    "Responde en español."
)


class PromptStrategy(ABC):
    """Contrato: transforma (pregunta, contexto) en una lista de mensajes."""

    name: str

    @abstractmethod
    def build(self, question: str, context: str) -> list[Message]: ...

    @staticmethod
    def _user_message(question: str, context: str) -> Message:
        return {"role": "user", "content": f"CONTEXTO:\n{context}\n\nPREGUNTA: {question}"}


class ZeroShotPrompt(PromptStrategy):
    """Zero-shot: instrucción directa, sin ejemplos."""

    name = "zero_shot"

    def build(self, question: str, context: str) -> list[Message]:
        return [{"role": "system", "content": SYSTEM_BASE}, self._user_message(question, context)]


class FewShotPrompt(PromptStrategy):
    """Few-shot: se muestran ejemplos de pregunta/respuesta para fijar formato y tono."""

    name = "few_shot"

    _EXAMPLES: list[Message] = [
        {"role": "user", "content": "CONTEXTO:\nLa biblioteca abre de 7am a 9pm.\n\nPREGUNTA: ¿Hasta qué hora abre la biblioteca?"},
        {"role": "assistant", "content": "Respuesta: Hasta las 9pm.\nFuente: documento sobre la biblioteca."},
        {"role": "user", "content": "CONTEXTO:\nLa matrícula cuesta 500.\n\nPREGUNTA: ¿Hay cafetería?"},
        {"role": "assistant", "content": "Respuesta: No tengo esa información en el contexto.\nFuente: ninguna."},
    ]

    def build(self, question: str, context: str) -> list[Message]:
        return [
            {"role": "system", "content": SYSTEM_BASE + " Usa el formato 'Respuesta: ... Fuente: ...'."},
            *self._EXAMPLES,
            self._user_message(question, context),
        ]


class ChainOfThoughtPrompt(PromptStrategy):
    """Chain-of-Thought: se pide razonar paso a paso antes de la respuesta final."""

    name = "chain_of_thought"

    def build(self, question: str, context: str) -> list[Message]:
        instruction = (
            SYSTEM_BASE
            + " Razona paso a paso: 1) identifica los datos relevantes del contexto, "
            "2) relaciónalos con la pregunta, 3) concluye. "
            "Termina con una línea 'Respuesta final: ...'."
        )
        return [{"role": "system", "content": instruction}, self._user_message(question, context)]


STRATEGIES: dict[str, PromptStrategy] = {
    s.name: s for s in (ZeroShotPrompt(), FewShotPrompt(), ChainOfThoughtPrompt())
}
