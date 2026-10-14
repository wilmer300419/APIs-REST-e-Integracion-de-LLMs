"""Técnicas de prompt engineering (patrón Strategy).

Cada técnica es una clase que sabe construir los mensajes para el LLM a
partir de la pregunta y del contexto recuperado por RAG. Los prompts están en
inglés y piden responder en el mismo idioma de la pregunta.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.llm.client import Message

SYSTEM_BASE = (
    "You are an academic assistant. Answer ONLY using the given CONTEXT. "
    "If the context does not contain the answer, say you do not have that information. "
    "Answer in the same language as the question."
)


class PromptStrategy(ABC):
    """Contrato: transforma (pregunta, contexto) en una lista de mensajes."""

    name: str

    @abstractmethod
    def build(self, question: str, context: str) -> list[Message]: ...

    @staticmethod
    def _user_message(question: str, context: str) -> Message:
        return {"role": "user", "content": f"CONTEXT:\n{context}\n\nQUESTION: {question}"}


class ZeroShotPrompt(PromptStrategy):
    """Zero-shot: instrucción directa, sin ejemplos."""

    name = "zero_shot"

    def build(self, question: str, context: str) -> list[Message]:
        return [{"role": "system", "content": SYSTEM_BASE}, self._user_message(question, context)]


class FewShotPrompt(PromptStrategy):
    """Few-shot: se muestran ejemplos de pregunta/respuesta para fijar formato y tono."""

    name = "few_shot"

    _EXAMPLES: list[Message] = [
        {"role": "user", "content": "CONTEXT:\nThe library is open from 7am to 9pm.\n\nQUESTION: What time does the library close?"},
        {"role": "assistant", "content": "Answer: It closes at 9pm.\nSource: library document."},
        {"role": "user", "content": "CONTEXT:\nTuition costs 500.\n\nQUESTION: Is there a cafeteria?"},
        {"role": "assistant", "content": "Answer: I do not have that information in the context.\nSource: none."},
    ]

    def build(self, question: str, context: str) -> list[Message]:
        return [
            {"role": "system", "content": SYSTEM_BASE + " Use the format 'Answer: ... Source: ...'."},
            *self._EXAMPLES,
            self._user_message(question, context),
        ]


class ChainOfThoughtPrompt(PromptStrategy):
    """Chain-of-Thought: se pide razonar paso a paso antes de la respuesta final."""

    name = "chain_of_thought"

    def build(self, question: str, context: str) -> list[Message]:
        instruction = (
            SYSTEM_BASE
            + " Reason step by step: 1) identify the relevant facts in the context, "
            "2) relate them to the question, 3) conclude. "
            "Finish with a line 'Final answer: ...'."
        )
        return [{"role": "system", "content": instruction}, self._user_message(question, context)]


STRATEGIES: dict[str, PromptStrategy] = {
    s.name: s for s in (ZeroShotPrompt(), FewShotPrompt(), ChainOfThoughtPrompt())
}
