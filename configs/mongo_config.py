import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class MongoConfig:
    uri: str
    database: str
    ankr_raw_collection: str
    binance_prices_collection: str
    asset_overviews_collection: str
    server_selection_timeout_ms: int


def load_mongo_config() -> MongoConfig:
    """Load MongoDB config from environment variables."""
    return MongoConfig(
        uri=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        database=os.getenv("MONGODB_DATABASE", "blockchain_mpc"),
        ankr_raw_collection=os.getenv("MONGODB_COLLECTION_ANKR_RAW", "ankr_raw_assets"),
        binance_prices_collection=os.getenv(
            "MONGODB_COLLECTION_BINANCE_PRICES",
            "binance_price_results",
        ),
        asset_overviews_collection=os.getenv(
            "MONGODB_COLLECTION_ASSET_OVERVIEWS",
            "asset_overviews",
        ),
        server_selection_timeout_ms=int(os.getenv("MONGODB_SERVER_SELECTION_TIMEOUT_MS", "5000")),
    )
