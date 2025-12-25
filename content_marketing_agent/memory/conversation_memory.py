"""Conversation and session memory utilities."""

from __future__ import annotations

from typing import List, Tuple

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage


class ConversationManager:
    """Thin wrapper around ChatMessageHistory to keep chat history clean."""

    def __init__(self, memory_key: str = "history", input_key: str = "input") -> None:
        self.memory_key = memory_key
        self.input_key = input_key
        self.chat_history = ChatMessageHistory()

    def load_history(self) -> List[BaseMessage]:
        """Return the current conversation history."""
        return self.chat_history.messages

    def append(self, user: str, ai: str) -> None:
        """Add a user/AI turn to the memory."""
        self.chat_history.add_message(HumanMessage(content=user))
        self.chat_history.add_message(AIMessage(content=ai))

    def reset(self) -> None:
        """Clear the memory buffer."""
        self.chat_history.clear()

    def as_tuples(self) -> List[Tuple[str, str]]:
        """Return history as (role, content) tuples for serialization."""
        tuples: List[Tuple[str, str]] = []
        for msg in self.load_history():
            role = "user" if msg.type == "human" else "assistant"
            content = msg.content if isinstance(msg.content, str) else str(msg.content)
            tuples.append((role, content))
        return tuples