"""MongoDB client and collection helpers."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

DEFAULT_URI = "mongodb://localhost:27017"
DEFAULT_DB = "content_blitz"


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient[Any]:
    """Return a cached MongoDB client."""
    uri = os.getenv("MONGO_URI", DEFAULT_URI)
    return MongoClient(uri, appname="content-blitz")


def get_database() -> Database[Any]:
    """Return the configured application database."""
    db_name = os.getenv("MONGO_DB_NAME", DEFAULT_DB)
    return get_mongo_client()[db_name]


def get_collection(name: str) -> Collection[Any]:
    """Return a typed collection by name."""
    return get_database()[name]


def ensure_indexes() -> None:
    """Create indexes needed for app queries."""
    db = get_database()
    db.projects.create_index([("created_at", DESCENDING)])
    db.chats.create_index([("project_id", ASCENDING), ("created_at", DESCENDING)])
    db.chats.create_index([("project_id", ASCENDING), ("title_generated", ASCENDING)])
    db.messages.create_index([("chat_id", ASCENDING), ("created_at", ASCENDING)])
    db.messages.create_index([("project_id", ASCENDING), ("created_at", ASCENDING)])
    db.research_outputs.create_index([("chat_id", ASCENDING)], unique=True)
