from __future__ import annotations

"""Brand voice persistence helpers."""

from datetime import datetime
from typing import Dict

from content_marketing_agent.data_access.database import get_collection

_COLLECTION = "brand_voice"
_DEFAULT_ID = "default"


def _collection():
    return get_collection(_COLLECTION)


def get_brand_voice() -> Dict[str, str]:
    """Return the saved brand voice profile or empty defaults."""
    doc = _collection().find_one({"_id": _DEFAULT_ID})
    if not doc:
        return {"brand": "", "tone": "", "audience": "", "guidelines": ""}
    return {
        "brand": doc.get("brand", ""),
        "tone": doc.get("tone", ""),
        "audience": doc.get("audience", ""),
        "guidelines": doc.get("guidelines", ""),
    }


def upsert_brand_voice(brand: str, tone: str, audience: str, guidelines: str) -> Dict[str, str]:
    """Create or update the singleton brand voice profile."""
    now = datetime.utcnow()
    payload = {
        "brand": (brand or "").strip(),
        "tone": (tone or "").strip(),
        "audience": (audience or "").strip(),
        "guidelines": (guidelines or "").strip(),
        "updated_at": now,
    }
    _collection().update_one(
        {"_id": _DEFAULT_ID},
        {"$set": payload, "$setOnInsert": {"created_at": now}},
        upsert=True,
    )
    payload.pop("updated_at", None)
    return payload
