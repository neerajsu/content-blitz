"""Chat detail view for a project's research flow."""

from __future__ import annotations

from typing import Any

import streamlit as st

from content_marketing_agent.graph.content_graph import build_research_graph, build_title_graph
from content_marketing_agent.state import get_project, set_active_chat, update_chat_summary, update_chat_title

DEFAULT_RESEARCH_MESSAGE = "Research something with the chatbot to populate this section."


@st.cache_resource
def _get_research_graph():
    """Cache the compiled research graph."""
    return build_research_graph()


@st.cache_resource
def _get_title_graph():
    """Cache the compiled title generation graph."""
    return build_title_graph()


def _ensure_chat_state(chat_id: str) -> tuple[list[tuple[str, str]], str]:
    histories = st.session_state.setdefault("chat_histories", {})
    outputs = st.session_state.setdefault("research_outputs", {})
    structured = st.session_state.setdefault("research_structured", {})
    if chat_id not in histories:
        histories[chat_id] = []
    if chat_id not in outputs:
        outputs[chat_id] = DEFAULT_RESEARCH_MESSAGE
    structured.setdefault(chat_id, {})
    return histories[chat_id], outputs[chat_id]


def _format_research_markdown(analysis: dict[str, Any]) -> str:
    summary = (analysis.get("summary") or "").strip() or "No summary available yet."
    keywords = analysis.get("keywords") or []
    insights = analysis.get("insights") or []
    references = analysis.get("references") or []

    lines = [
        "### Summary",
        summary,
        "",
        "### Keywords",
    ]
    if keywords:
        lines.extend(f"- {kw}" for kw in keywords)
    else:
        lines.append("- None captured yet.")

    lines.extend(["", "### Insights"])
    if insights:
        lines.extend(f"- {item}" for item in insights)
    else:
        lines.append("- No insights yet.")

    lines.extend(["", "### References"])
    if references:
        for idx, ref in enumerate(references, 1):
            title = ref.get("title") or "Reference"
            url = ref.get("url") or ""
            snippet = ref.get("snippet") or ""
            link = f"[{title}]({url})" if url else title
            if snippet:
                lines.append(f"{idx}. {link} - {snippet}")
            else:
                lines.append(f"{idx}. {link}")
    else:
        lines.append("No references yet.")

    return "\n".join(lines)


def _update_chat_summary(project_id: str, chat_id: str, summary: str) -> None:
    update_chat_summary(project_id, chat_id, summary)


def _generate_title_from_summary(summary: str) -> str:
    """Create a concise title from the research summary using the title graph."""
    text = (summary or "").strip()
    if not text:
        return ""
    try:
        graph = _get_title_graph()
        state = graph.invoke({"summary": text})
        title = state.get("title", "") if isinstance(state, dict) else ""
        title = (title or "").strip()
        if title:
            return title
    except Exception:
        pass
    fallback = text.splitlines()[0].strip()
    if len(fallback) > 60:
        fallback = fallback[:60].rsplit(" ", 1)[0]
    return fallback or "Untitled chat"


def _maybe_set_title(project_id: str, chat_id: str, summary: str) -> None:
    """Set an auto-generated title once, if not already set or edited by the user."""
    project = get_project(project_id)
    if not project:
        return
    chat = next((c for c in project["chats"] if c.get("id") == chat_id), None)
    if not chat:
        return
    already_set = chat.get("title_generated")
    existing_title = (chat.get("title") or "").strip()
    if not already_set and not existing_title:
        generated = _generate_title_from_summary(summary)
        if generated:
            update_chat_title(project_id, chat_id, generated, generated=True)
    else:
        fallback_title = existing_title or "Untitled chat"
        update_chat_title(project_id, chat_id, fallback_title, generated=bool(already_set))


def render_chat_detail(selected_chat: dict, project_id: str) -> None:
    """Render the two-column chat + research output view for a selected chat."""
    chat_id = selected_chat.get("id", "unknown")
    chat_history, research_markdown = _ensure_chat_state(chat_id)
    input_key = f"project_chat_input_{chat_id}"
    reset_flag = f"{input_key}_reset"

    back_col, _ = st.columns([0.2, 0.8])
    with back_col:
        if st.button("< Back to chats", key="back_to_chats"):
            set_active_chat(None)
            st.rerun()

    if st.session_state.get(reset_flag):
        # Clear the text area state before rendering the widget
        st.session_state[input_key] = ""
        st.session_state[reset_flag] = False

    st.markdown(f"**{selected_chat.get('title', 'Chat')}**")

    chat_col, research_col = st.columns([1.1, 1.3])
    with chat_col:
        st.subheader("Chat")
        chat_container = st.container(height=400, border=True)
        with chat_container:
            for role, msg in chat_history:
                if role.lower() in {"you", "user"}:
                    chat_container.chat_message("user").write(msg)
                else:
                    chat_container.chat_message("assistant").write(msg)

        with st.form(key=f"chat_form_{chat_id}", clear_on_submit=False):
            user_input = st.text_area(
                "Enter your prompt",
                key=input_key,
                placeholder="Type to continue the chat",
                height=140,
                max_chars=None,
            )
            submitted = st.form_submit_button("Submit")
            if submitted:
                trimmed = user_input.strip()
                if not trimmed:
                    st.warning("Please enter a prompt before submitting.")
                else:
                    previous_output = st.session_state.research_outputs.get(chat_id, DEFAULT_RESEARCH_MESSAGE)
                    has_real_research = bool(previous_output and previous_output != DEFAULT_RESEARCH_MESSAGE)
                    current_output = "" if not has_real_research else previous_output
                    research_output_for_guard = previous_output if has_real_research else ""
                    chat_history.append(("user", trimmed))
                    st.session_state.chat_histories[chat_id] = chat_history
                    MAX_TURNS = 4  # 2 user + 2 assistant
                    recent_history = chat_history[-MAX_TURNS:]
                    history_text = "\n".join(f"{role}: {message}" for role, message in recent_history)

                    with st.spinner("Research agent is updating your output..."):
                        graph = _get_research_graph()
                        state = graph.invoke(
                            {
                                "prompt": trimmed,
                                "history": history_text,
                                "current_output": current_output,
                                "research_output": research_output_for_guard,
                            }
                        )
                    allowed = state.get("allowed", True) if isinstance(state, dict) else True
                    if not allowed:
                        chat_history.append(
                            (
                                "assistant",
                                "Your question is regarding a different domain to what you are currently researching. Please use a different chat.",
                            )
                        )
                        st.session_state.chat_histories[chat_id] = chat_history
                        st.session_state[reset_flag] = True
                        st.rerun()

                    result = state.get("result", {}) if isinstance(state, dict) else {}
                    analysis = result.get("analysis", {})
                    research_markdown = _format_research_markdown(analysis)
                    st.session_state.research_outputs[chat_id] = research_markdown
                    st.session_state.research_structured[chat_id] = analysis
                    chat_history.append(("assistant", "Research output updated. Let me know if you want to tweak anything else."))
                    st.session_state.chat_histories[chat_id] = chat_history
                    _maybe_set_title(project_id, chat_id, analysis.get("summary", ""))
                    _update_chat_summary(project_id, chat_id, analysis.get("summary", ""))
                    st.session_state[reset_flag] = True
                    st.rerun()

    with research_col:
        header_col, reset_col = st.columns([0.8, 0.2])
        with header_col:
            st.subheader("Research Output")
        with reset_col:
            if st.button("Start fresh", key=f"reset_research_{chat_id}"):
                st.session_state.research_outputs[chat_id] = DEFAULT_RESEARCH_MESSAGE
                st.session_state.research_structured.pop(chat_id, None)
                research_markdown = DEFAULT_RESEARCH_MESSAGE

        output_box = st.container(height=480, border=True)
        with output_box:
            st.markdown(research_markdown)
