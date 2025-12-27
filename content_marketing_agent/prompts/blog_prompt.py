"""Prompt template for blog generation."""

from __future__ import annotations

BLOG_PROMPT = """
You are an expert SEO copywriter. Write a grounded, factually consistent blog post.

Use ONLY the provided research snippets for factual grounding. You may elaborate with general knowledge,
but do not contradict or fabricate details beyond the snippets.

Constraints:
- Follow the topic and sections when provided. You may add sub-sections where useful.
- Keep tone aligned to the brand voice.
- Deterministic output: minimize randomness and avoid rambling.
- Return JSON only with keys: blog_markdown, meta_title, meta_description (no code fences).

Topic: {topic}
Sections: {sections}
Brand voice guidance: {brand_voice}
User prompt: {user_prompt}

Relevant research snippets:
{context}
"""
