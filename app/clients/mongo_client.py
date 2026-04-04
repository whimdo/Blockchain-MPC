from __future__ import annotations

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from app.utils.logging_config import get_logger
from configs.mongo_config import load_mongo_config


class MongoDBClient:
    """MongoDB client wrapper for shared DB access."""

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.mongo_client")
        self.config = load_mongo_config()
        self._client = MongoClient(
            self.config.uri,
            serverSelectionTimeoutMS=self.config.server_selection_timeout_ms,
        )
        self._database: Database = self._client[self.config.database]

    def ping(self) -> None:
        """Check MongoDB connection."""
        self._client.admin.command("ping")

    @property
    def db(self) -> Database:
        return self._database

    def collection(self, name: str) -> Collection:
        return self._database[name]
