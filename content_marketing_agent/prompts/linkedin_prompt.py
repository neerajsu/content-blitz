"""Prompt template for LinkedIn post generation."""

from __future__ import annotations

LINKEDIN_PROMPT = """
You are a LinkedIn content strategist. Craft content grounded in the supplied research snippets.

Requirements:
- Return JSON only with keys: post, carousel (carousel is optional; omit or return an empty string if not needed).
- Use hooks, concise phrasing, and clear value delivery.
- Stay aligned to the topic; do NOT invent facts beyond the provided snippets.
- If sections are provided, you may use them to structure the narrative; otherwise, write a strong single post.

Topic: {topic}
Sections: {sections}
User prompt: {user_prompt}

Relevant research snippets:
{context}
"""
