"""Prompt template for LinkedIn post generation."""

from __future__ import annotations

LINKEDIN_PROMPT = """You are a LinkedIn content strategist.
Create a LinkedIn post using the provided blog or research content.
Return JSON with keys: post, carousel (optional field for multi-slide outline).

Tone should be optimized for engagement (hooks, concise, value-first).

Source content:
{source}
"""
