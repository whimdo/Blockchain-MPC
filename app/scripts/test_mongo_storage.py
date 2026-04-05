from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.storage.market_storage import MarketStorage  # noqa: E402
from configs.mongo_config import load_mongo_config  # noqa: E402


def main() -> int:
    storage = MarketStorage()
    config = load_mongo_config()

    storage.mongo_client.ping()
    print(f"[OK] MongoDB connection success. db={config.database}")

    ankr_id = storage.save_ankr_raw_assets(
        address="0xTEST_ADDRESS",
        chains=["eth", "bsc"],
        ankr_result={"assets": [{"symbol": "USDT", "balance": "100.0"}]},
    )
    binance_id = storage.save_binance_prices(
        symbols=["BTCUSDT", "ETHUSDT"],
        prices_result={"BTCUSDT": "67000", "ETHUSDT": "3400"},
    )
    overview_id = storage.save_asset_overview(
        address="0xTEST_ADDRESS",
        chains=["eth", "bsc"],
        overview_result={
            "total_usd": "12345.67",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    inserted = [
        (config.ankr_raw_collection, ankr_id),
        (config.binance_prices_collection, binance_id),
        (config.asset_overviews_collection, overview_id),
    ]

    for collection_name, inserted_id in inserted:
        document = storage.mongo_client.collection(collection_name).find_one(
            {"_id": ObjectId(inserted_id)}
        )
        if document is None:
            raise RuntimeError(
                f"Verification failed: document not found in {collection_name}, _id={inserted_id}"
            )
        print(f"[OK] Insert+Query passed. collection={collection_name}, _id={inserted_id}")

    # for collection_name, inserted_id in inserted:
    #     storage.mongo_client.collection(collection_name).delete_one({"_id": ObjectId(inserted_id)})
    #     print(f"[OK] Cleanup done. collection={collection_name}, _id={inserted_id}")

    print("[DONE] Mongo storage test passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
