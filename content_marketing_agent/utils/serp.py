"""SERP API utility with graceful fallback when no key is provided."""

from __future__ import annotations

import os
from typing import Any, Dict, List

import requests


def search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a web search using SERP API when available, otherwise return stubbed data.

    Args:
        query: Search query string.
        num_results: Number of desired results.

    Returns:
        List of result dictionaries containing title, link, and snippet.
    """
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return [
            {
                "title": f"Stub result {i + 1} for '{query}'",
                "link": f"https://example.com/{i + 1}",
                "snippet": "Configure SERPAPI_API_KEY to fetch real-time search results.",
            }
            for i in range(num_results)
        ]

    params = {
        "engine": "google",
        "q": query,
        "num": num_results,
        "api_key": api_key,
    }
    response = requests.get("https://serpapi.com/search", params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    organic_results = payload.get("organic_results", [])[:num_results]
    results: List[Dict[str, Any]] = []
    for item in organic_results:
        results.append(
            {
                "title": item.get("title"),
                "link": item.get("link"),
                "snippet": item.get("snippet") or item.get("summary"),
            }
        )
    return results
