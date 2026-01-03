from __future__ import annotations

"""LinkedIn publishing helpers."""

import logging
import os
from typing import Any, Dict

import requests

logger = logging.getLogger(__name__)

LINKEDIN_POST_URL = "https://api.linkedin.com/v2/ugcPosts"


def _get_author_urn() -> str:
    author = os.getenv("LINKEDIN_AUTHOR_URN", "").strip()
    if not author:
        raise ValueError("LinkedIn author URN is not configured.")
    return author


def _get_access_token() -> str:
    token = os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip()
    if not token:
        raise ValueError("LinkedIn access token is not configured.")
    return token


def publish_linkedin_post(post_text: str) -> Dict[str, Any]:
    """Publish a LinkedIn post using the LinkedIn API.

    Carousel data is intentionally ignored; only the main post text is sent.
    """
    text = (post_text or "").strip()
    if not text:
        raise ValueError("LinkedIn post content is empty.")

    author = _get_author_urn()
    token = _get_access_token()

    payload = {
        "author": author,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(LINKEDIN_POST_URL, headers=headers, json=payload, timeout=15)
    except requests.RequestException as exc:  # pragma: no cover - network call
        logger.warning("LinkedIn publish request failed: %s", exc)
        raise RuntimeError(f"LinkedIn publish request failed: {exc}") from exc

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:  # pragma: no cover - network call
        logger.warning("LinkedIn publish failed (%s): %s", response.status_code, response.text)
        raise RuntimeError(f"LinkedIn API error {response.status_code}: {response.text}") from exc

    try:
        data: Dict[str, Any] = response.json()
    except ValueError:
        data = {"raw_response": response.text}

    logger.info("LinkedIn post published for author %s", author)
    return data
