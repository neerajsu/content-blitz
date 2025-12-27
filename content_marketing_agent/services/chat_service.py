"""Chat service orchestrating repositories for chats, messages, and research outputs."""

from __future__ import annotations

from typing import Any, Optional

from content_marketing_agent.data_access import chat_repository, message_repository, research_repository


def list_chats(project_id: str) -> list[dict[str, Any]]:
    return chat_repository.list_chats(project_id)


def get_chat(chat_id: Optional[str]) -> Optional[dict[str, Any]]:
    if not chat_id:
        return None
    return chat_repository.get_chat(chat_id)


def add_new_chat(project_id: str, default_research_message: str) -> Optional[dict[str, Any]]:
    chat = chat_repository.create_chat(project_id)
    research_repository.upsert_research_output(
        project_id=project_id,
        chat_id=chat["id"],
        markdown=default_research_message,
        structured={},
        summary=default_research_message,
    )
    return chat


def delete_chat(project_id: str, chat_id: str) -> None:
    chat_repository.delete_chat(chat_id)
    message_repository.delete_messages_for_chat(chat_id)
    research_repository.delete_research_output(chat_id)


def update_chat_title(chat_id: str, title: str, generated: bool = False) -> None:
    trimmed_title = (title or "").strip() or "Untitled chat"
    chat_repository.update_chat_title(chat_id, trimmed_title, generated=generated)


def update_chat_summary(chat_id: str, summary: str) -> None:
    trimmed = (summary or "").strip()
    if not trimmed:
        return
    snippet = trimmed.splitlines()[0][:120]
    chat_repository.update_chat_summary(chat_id, snippet)


def add_message(project_id: str, chat_id: str, role: str, content: str) -> dict[str, Any]:
    return message_repository.add_message(project_id, chat_id, role, content)


def get_chat_messages(chat_id: str) -> list[dict[str, Any]]:
    return message_repository.list_messages(chat_id)


def get_chat_research_output(chat_id: str, default_message: str) -> dict[str, Any]:
    existing = research_repository.get_research_output(chat_id)
    if existing:
        return existing
    return {"chat_id": chat_id, "markdown": default_message, "structured": {}, "summary": default_message}


def save_research_output(
    project_id: str, chat_id: str, markdown: str, structured: dict[str, Any], summary: str
) -> dict[str, Any]:
    return research_repository.upsert_research_output(project_id, chat_id, markdown, structured, summary)
