from __future__ import annotations

from datetime import datetime, timezone

from app.clients.milvus_client import MilvusClient
from app.clients.mongo_client import MongoDBClient
from app.models.snapshot_models import SnapshotProposal, SnapshotProposalVector
from app.utils.logging_config import get_logger
from configs.milvus_config import load_milvus_config
from configs.mongo_config import load_mongo_config


class SnapshotStorage:
    """Storage layer for Snapshot proposals (MongoDB) and vectors (Milvus)."""

    def __init__(self) -> None:
        """初始化 MongoDB/Milvus 客户端与配置。"""
        self.logger = get_logger("app.storage.snapshot_storage")
        self.mongo_config = load_mongo_config()
        self.milvus_config = load_milvus_config()
        self.mongo_client = MongoDBClient()
        self.milvus_client = MilvusClient()

    @staticmethod
    def _now_utc() -> datetime:
        """返回当前 UTC 时间。"""
        return datetime.now(timezone.utc)

    def save_snapshot_proposal(self, proposal: SnapshotProposal) -> str:
        """
        将 SnapshotProposal 存入 MongoDB。

        规则：
        - 使用 proposal_id 作为 MongoDB 文档主键 `_id`
        - 重复 proposal_id 时进行 upsert 覆盖更新
        """
        if not proposal.proposal_id:
            raise ValueError("proposal.proposal_id cannot be empty")

        now = self._now_utc()
        payload = proposal.to_dict()
        payload["_id"] = proposal.proposal_id
        payload["updated_at"] = now

        self.mongo_client.collection(
            self.mongo_config.snapshot_proposals_collection
        ).update_one(
            {"_id": proposal.proposal_id},
            {
                "$set": payload,
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

        self.logger.info(
            "Stored Snapshot proposal _id=%s collection=%s",
            proposal.proposal_id,
            self.mongo_config.snapshot_proposals_collection,
        )
        return proposal.proposal_id

    def save_snapshot_proposal_vector(
        self,
        proposal_vector: SnapshotProposalVector,
        flush: bool = True,
    ) -> int:
        """
        将 SnapshotProposalVector 存入 Milvus proposals collection。

        返回值为写入条数（通常为 1）。
        """
        payload = proposal_vector.to_dict()
        collection = self.milvus_client.collection(self.milvus_config.collection_proposals)
        result = collection.insert([payload])

        if flush:
            collection.flush()

        inserted = len(getattr(result, "primary_keys", [])) or 1
        self.logger.info(
            "Stored Snapshot proposal vector proposal_id=%s collection=%s rows=%s",
            proposal_vector.proposal_id,
            self.milvus_config.collection_proposals,
            inserted,
        )
        return inserted
