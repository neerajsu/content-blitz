"""Prompt for routing user intent."""

from __future__ import annotations

ROUTER_PROMPT = """You are an intent classifier for a content marketing assistant.
Classify the user request into one of: research, blog, linkedin, image, mixed.
Respond with a single label and a short rationale in JSON.
Example: {"intent": "blog", "reason": "User asked for a long-form article"}.
"""
