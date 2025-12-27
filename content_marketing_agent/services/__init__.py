"""Service layer for the content marketing agent."""

from content_marketing_agent.services.project_service import create_project, get_project, list_projects, update_project_title
from content_marketing_agent.services.chat_service import (
    add_message,
    add_new_chat,
    delete_chat,
    get_chat,
    get_chat_messages,
    get_chat_research_output,
    list_chats,
    save_research_output,
    update_chat_summary,
    update_chat_title,
)
from content_marketing_agent.services.bootstrap import bootstrap_storage
from . import vector_service as vector_service  # noqa: F401 - re-export for convenience
