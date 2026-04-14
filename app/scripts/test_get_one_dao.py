from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.clients.snapshot_client import SnapshotClient
from app.services.snapshot_service import SnapshotService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_get_one_dao")


def save_raw_data(raw_data: dict, space_id: str, output_dir: str = "data/raw") -> Path:
    """
    保存原始数据到文件
    
    Args:
        raw_data: 原始提案数据
        space_id: DAO 空间 ID
        output_dir: 输出目录，默认为 data/raw
    
    Returns:
        保存的文件路径
    """
    # 创建输出目录
    save_path = ROOT_DIR / output_dir
    save_path.mkdir(parents=True, exist_ok=True)
    
    # 生成文件名：空间ID_提案ID_时间戳.json
    proposal_id = raw_data.get("id", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{space_id}_{proposal_id}_{timestamp}.json"
    filepath = save_path / filename
    
    # 保存数据
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Raw data saved to: {filepath}")
    return filepath


def main() -> None:
    """
    Simple smoke test:
    1. fetch one proposal from Snapshot by DAO space
    2. normalize it via SnapshotService
    3. save raw data to file
    """
    primary_space_id = os.getenv("SNAPSHOT_TEST_SPACE_ID", "").strip()
    candidate_space_ids = [
        item.strip()
        for item in os.getenv(
            "SNAPSHOT_TEST_SPACE_CANDIDATES",
            "aave.eth,uniswapgovernance.eth,ens.eth",
        ).split(",")
        if item.strip()
    ]
    if primary_space_id:
        candidate_space_ids = [primary_space_id] + [
            item for item in candidate_space_ids if item != primary_space_id
        ]

    client = SnapshotClient()
    service = SnapshotService()

    try:
        logger.info(
            "Snapshot DAO smoke test started. candidates=%s",
            candidate_space_ids,
        )

        raw_items = []
        space_id = ""
        for candidate in candidate_space_ids:
            raw_items = client.get_proposals_by_space(
                space_id=candidate,
                first=1,
                skip=0,
                detail_level="full",
            )
            if raw_items:
                space_id = candidate
                break

        if not raw_items:
            raise RuntimeError(
                "No proposals found for all test spaces: "
                + ",".join(candidate_space_ids)
            )

        raw = raw_items[0]
        
        # ========== 新增：保存 raw 数据到文件 ==========
        saved_path = save_raw_data(raw, space_id)
        print(f"\n[SAVED] Raw data saved to: {saved_path}")
        # ===========================================
        
        print("[RAW]")
        print(f"space_id={space_id}")
        print(f"proposal_id={raw.get('id')}")
        print(f"title={raw.get('title')}")
        print(f"state={raw.get('state')}")
        print(f"created={raw.get('created')}")
        print(f"link={raw.get('link')}")

        normalized = service.normalize_proposal(raw)
        print("\n[NORMALIZED]")
        print(f"proposal_id={normalized.proposal_id}")
        print(f"space_id={normalized.space_id}")
        print(f"title={normalized.title}")
        print(f"state={normalized.state}")
        print(f"keywords={normalized.keywords}")

        logger.info(
            "Snapshot DAO smoke test passed. space_id=%s proposal_id=%s",
            space_id,
            normalized.proposal_id,
        )
        print("\n[DONE] Snapshot get-one-dao test passed.")
    except Exception:
        logger.exception("Snapshot DAO smoke test failed. space_id=%s", space_id)
        raise


if __name__ == "__main__":
    main()