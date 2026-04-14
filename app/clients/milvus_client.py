from __future__ import annotations

from pymilvus import Collection, connections, utility

from app.utils.logging_config import get_logger
from configs.milvus_config import load_milvus_config


class MilvusDBClient:
    """Milvus client wrapper for shared vector DB access."""

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.milvus_client")
        self.config = load_milvus_config()
        self.alias = "default"

        connect_kwargs: dict[str, str] = {
            "alias": self.alias,
            "uri": self.config.uri,
        }
        if self.config.token:
            connect_kwargs["token"] = self.config.token

        connections.connect(**connect_kwargs)

    def ping(self) -> None:
        """Check Milvus connection."""
        utility.list_collections(using=self.alias)

    def collection(self, name: str | None = None) -> Collection:
        if name is None:
            self.logger.warning("No collection name provided, using 'error' as default to prevent accidental data issues.")
            name = self.config.collection
        collection_name = name
        return Collection(name=collection_name, using=self.alias)


MilvusClient = MilvusDBClient
