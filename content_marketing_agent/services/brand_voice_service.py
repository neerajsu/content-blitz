from __future__ import annotations

"""Brand voice service for saving and retrieving tone guidance."""

from typing import Dict

from content_marketing_agent.data_access import brand_voice_repository


def get_brand_voice() -> Dict[str, str]:
    """Return the saved brand voice profile or defaults."""
    return brand_voice_repository.get_brand_voice()


def save_brand_voice(brand: str, tone: str, audience: str, guidelines: str) -> Dict[str, str]:
    """Persist the brand voice profile and return the stored values."""
    return brand_voice_repository.upsert_brand_voice(brand, tone, audience, guidelines)
