"""Service bootstrap helpers."""

from __future__ import annotations

from functools import lru_cache

from content_marketing_agent.data_access.database import ensure_indexes


@lru_cache(maxsize=1)
def bootstrap_storage() -> None:
    """Ensure indexes exist once per process."""
    ensure_indexes()
