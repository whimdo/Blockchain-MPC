import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class MilvusConfig:
    uri: str
    token: str
    database: str
    collection: str
    collection_proposals: str
    timeout_seconds: int


def load_milvus_config() -> MilvusConfig:
    """Load Milvus config from environment variables."""
    return MilvusConfig(
        uri=os.getenv("MILVUS_URI", "http://localhost:19530").rstrip("/"),
        token=os.getenv("MILVUS_TOKEN", ""),
        database=os.getenv("MILVUS_DATABASE", "default"),
        collection= "error",
        collection_proposals=os.getenv("MILVUS_COLLECTION_PROPOSALS", "proposals_vectors"),
        timeout_seconds=int(os.getenv("MILVUS_TIMEOUT_SECONDS", "30")),
    )
