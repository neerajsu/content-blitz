"""Prompt template for blog generation."""

from __future__ import annotations

BLOG_PROMPT = """You are an expert SEO copywriter.
Write a markdown blog post using the research summary and brand voice.
Include: H1 title, H2/H3 structure, bullets, and a short conclusion.
Return JSON with keys: blog_markdown, meta_title, meta_description.

Brand voice guidance:
{brand_voice}

Research summary:
{research_summary}
"""
