import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class SnapshotConfig:
    snapshot_graphql_url: str
    space_ids: list[str]
    fetch_first: int
    fetch_state: str
    fetch_detail_level: str
    poll_interval_seconds: int
    max_seen_ids: int


def load_snapshot_config() -> SnapshotConfig:
    """Load Snapshot polling config from environment variables."""
    raw_space_ids = os.getenv("SNAPSHOT_SPACE_IDS", "")
    space_ids = [item.strip() for item in raw_space_ids.split(",") if item.strip()]

    return SnapshotConfig(
        snapshot_graphql_url=os.getenv(
            "SNAPSHOT_GRAPHQL_URL",
            "https://hub.snapshot.org/graphql",
        ).rstrip("/"),
        space_ids=space_ids,
        fetch_first=int(os.getenv("SNAPSHOT_FETCH_FIRST", "20")),
        fetch_state=os.getenv("SNAPSHOT_FETCH_STATE", "").strip(),
        fetch_detail_level=os.getenv("SNAPSHOT_FETCH_DETAIL_LEVEL", "full").strip(),
        poll_interval_seconds=int(os.getenv("SNAPSHOT_POLL_INTERVAL_SECONDS", "60")),
        max_seen_ids=int(os.getenv("SNAPSHOT_MAX_SEEN_IDS", "10000")),
    )