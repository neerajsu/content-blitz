"""Prompt template for research summarization."""

from __future__ import annotations

RESEARCH_PROMPT = """You are a research analyst. Given web results, create:
- A concise summary (<=150 words)
- A bullet list of 8-12 SEO keywords
- 3-5 key insights
Return JSON with keys: summary, keywords, insights.
Don't include the "```json" code fence in the response
Web results:
{results}
"""
