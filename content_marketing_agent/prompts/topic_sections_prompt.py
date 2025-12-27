"""Prompt for extracting explicit topic and sections from the user prompt."""

from __future__ import annotations

TOPIC_SECTIONS_PROMPT = """
You extract a topic and any explicit section headings from the user's prompt.

Rules:
- Remove generic platform labels like "LinkedIn" or "blog" (any casing) from the topic text.
- Only return a topic if the user explicitly mentioned one. Do NOT invent a topic.
- Only return sections if the user explicitly listed them. Do NOT invent sections.
- If nothing is provided, return empty strings/arrays.

Output strict JSON: {"topic": "<topic or empty string>", "sections": ["...", "..."]}.
"""
