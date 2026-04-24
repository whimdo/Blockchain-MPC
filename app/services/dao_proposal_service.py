from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.clients.kafka_client import KafkaClient
from app.clients.mongo_client import MongoDBClient
from app.clients.snapshot_client import SnapshotClient
from app.models.dao_proposal import (
    DAO,
    DAOOverviewResponse,
    DetailAndSimilarProposalsResponse,
    DetailProposal,
    DynamicSynchronousProposalResponse,
    ProposalListInDAOResponse,
    ProposalListItem,
    SimilarProposals,
)
from app.utils.logging_config import get_logger
from configs.kafka_config import load_kafka_config
from configs.mongo_config import load_mongo_config


class DaoProposalServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class DaoProposalService:
    def __init__(self) -> None:
        self.logger = get_logger("app.services.dao_proposal_service")
        self._mongo = MongoDBClient()
        self._mongo_cfg = load_mongo_config()
        self._kafka_cfg = load_kafka_config()
        self._snapshot_client = SnapshotClient()
        self._kafka_client = KafkaClient()
        self._dao_spaces_config = Path(__file__).resolve().parents[2] / "configs" / "dao_spaces_config.yaml"

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _to_iso_utc(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return str(value)

    def _load_dao_spaces_config(self) -> dict[str, Any]:
        if not self._dao_spaces_config.exists():
            raise DaoProposalServiceError(500, "DAO_CONFIG_NOT_FOUND", "DAO config file not found.")

        with self._dao_spaces_config.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise DaoProposalServiceError(500, "DAO_CONFIG_INVALID", "DAO config format is invalid.")
        return data

    def _visible_dao_spaces(self) -> list[dict[str, Any]]:
        cfg = self._load_dao_spaces_config()
        spaces = cfg.get("dao_spaces") or []
        if not isinstance(spaces, list):
            return []

        visible: list[dict[str, Any]] = []
        for item in spaces:
            if not isinstance(item, dict):
                continue
            if not item.get("enabled", True):
                continue
            if not item.get("show_on_dao_dashboard", True):
                continue
            visible.append(item)

        visible.sort(key=lambda x: int(x.get("sort_order", 10**9)))
        return visible

    def _find_visible_dao(self, space_id: str) -> dict[str, Any]:
        sid = (space_id or "").strip()
        if not sid:
            raise DaoProposalServiceError(400, "SPACE_ID_REQUIRED", "Field 'space_id' is required.")

        dao_cfg = next(
            (item for item in self._visible_dao_spaces() if str(item.get("space_id", "")).strip() == sid),
            None,
        )
        if dao_cfg is None:
            raise DaoProposalServiceError(404, "DAO_NOT_FOUND", "DAO configuration not found.")
        return dao_cfg

    def _proposal_collection_name(self) -> str:
        return self._mongo_cfg.snapshot_proposals_collection

    @staticmethod
    def _proposal_doc_to_list_item(doc: dict[str, Any]) -> ProposalListItem:
        proposal_id = str(doc.get("proposal_id") or doc.get("_id") or "")
        return ProposalListItem(
            proposal_id=proposal_id,
            space_id=str(doc.get("space_id", "")),
            author=doc.get("author"),
            title=str(doc.get("title", "")),
            state=str(doc.get("state", "")),
        )

    @staticmethod
    def _proposal_doc_to_detail(doc: dict[str, Any]) -> DetailProposal:
        proposal_id = str(doc.get("proposal_id") or doc.get("_id") or "")
        return DetailProposal(
            proposal_id=proposal_id,
            space_id=str(doc.get("space_id", "")),
            space_name=doc.get("space_name"),
            title=str(doc.get("title", "")),
            body=str(doc.get("body", "")),
            discussion=doc.get("discussion"),
            author=doc.get("author"),
            state=doc.get("state"),
            start=doc.get("start"),
            end=doc.get("end"),
            snapshot=doc.get("snapshot"),
            choices=list(doc.get("choices", []) or []),
            scores=list(doc.get("scores", []) or []),
            scores_total=doc.get("scores_total"),
            scores_updated=doc.get("scores_updated"),
            created=doc.get("created"),
            link=doc.get("link"),
            source=str(doc.get("source", "snapshot")),
            cleaned_text=doc.get("cleaned_text"),
            keywords=list(doc.get("keywords", []) or []),
        )

    def get_dao_overview(self) -> DAOOverviewResponse:
        collection = self._mongo.collection(self._proposal_collection_name())
        daos: list[DAO] = []

        for dao_cfg in self._visible_dao_spaces():
            space_id = str(dao_cfg.get("space_id", "")).strip()
            if not space_id:
                continue

            synchronized_count = collection.count_documents({"space_id": space_id})
            latest_doc = collection.find_one(
                {"space_id": space_id},
                sort=[("updated_at", -1), ("created", -1)],
                projection={"updated_at": 1, "created": 1},
            )
            latest_sync = None
            if latest_doc:
                latest_sync = self._to_iso_utc(latest_doc.get("updated_at") or latest_doc.get("created"))

            daos.append(
                DAO(
                    name=str(dao_cfg.get("display_name") or dao_cfg.get("name") or space_id),
                    space_id=space_id,
                    logo=dao_cfg.get("logo"),
                    description=dao_cfg.get("description"),
                    tags=list(dao_cfg.get("tags", []) or []),
                    enabled=bool(dao_cfg.get("enabled", True)),
                    latest_synchronization_time=latest_sync,
                    synchronized_proposals_count=synchronized_count,
                )
            )

        return DAOOverviewResponse(page_updated_at=self._utc_now_iso(), dao_count=len(daos), daos=daos)

    def get_proposals_in_dao(self, space_id: str, page: int, page_size: int) -> ProposalListInDAOResponse:
        sid = (space_id or "").strip()
        if not sid:
            raise DaoProposalServiceError(400, "SPACE_ID_REQUIRED", "Path parameter 'space_id' is required.")

        dao_cfg = self._find_visible_dao(sid)
        collection = self._mongo.collection(self._proposal_collection_name())
        skip = (page - 1) * page_size
        cursor = collection.find(
            {"space_id": sid},
            sort=[("created", -1), ("updated_at", -1)],
            skip=skip,
            limit=page_size,
        )
        proposals = [self._proposal_doc_to_list_item(doc) for doc in cursor]

        return ProposalListInDAOResponse(
            page_updated_at=self._utc_now_iso(),
            space_id=sid,
            dao_name=str(dao_cfg.get("display_name") or dao_cfg.get("name") or sid),
            page=page,
            page_size=page_size,
            proposals=proposals,
        )

    def get_proposal_detail_and_similar(self, proposal_id: str, top_k: int) -> DetailAndSimilarProposalsResponse:
        pid = (proposal_id or "").strip()
        if not pid:
            raise DaoProposalServiceError(400, "PROPOSAL_ID_REQUIRED", "Path parameter 'proposal_id' is required.")

        collection = self._mongo.collection(self._proposal_collection_name())
        doc = collection.find_one({"$or": [{"proposal_id": pid}, {"_id": pid}]})
        if doc is None:
            raise DaoProposalServiceError(404, "PROPOSAL_NOT_FOUND", "Proposal not found.")

        detail = self._proposal_doc_to_detail(doc)
        similar_cursor = collection.find(
            {"proposal_id": {"$ne": detail.proposal_id}},
            sort=[("created", -1), ("updated_at", -1)],
            limit=top_k,
        )
        similar_items = [self._proposal_doc_to_list_item(item) for item in similar_cursor]

        return DetailAndSimilarProposalsResponse(
            proposal=detail,
            similar_proposals=SimilarProposals(
                proposal_id=detail.proposal_id,
                space_id=detail.space_id,
                top_k=top_k,
                similar_proposals=similar_items,
            ),
        )

    def dynamic_sync_proposals(self, space_id: str, latest_k: int) -> DynamicSynchronousProposalResponse:
        sid = (space_id or "").strip()
        if not sid:
            raise DaoProposalServiceError(400, "SPACE_ID_REQUIRED", "Field 'space_id' is required.")

        self._find_visible_dao(sid)
        latest_k = max(1, int(latest_k or 10))

        latest_proposals = self._snapshot_client.get_proposals_by_space(
            space_id=sid,
            first=latest_k,
            skip=0,
            detail_level="full",
            state=None,
        )

        collection = self._mongo.collection(self._proposal_collection_name())
        producer = self._kafka_client.producer()
        pushed_items: list[ProposalListItem] = []
        topic = self._kafka_cfg.topic_dao_to_vector

        try:
            for proposal in latest_proposals:
                if not isinstance(proposal, dict):
                    continue

                proposal_id = str(proposal.get("id", "")).strip()
                if not proposal_id:
                    continue

                exists = collection.find_one(
                    {"$or": [{"proposal_id": proposal_id}, {"_id": proposal_id}]},
                    projection={"_id": 1},
                )
                if exists is not None:
                    continue

                message = {
                    "source": "snapshot",
                    "space_id": sid,
                    "fetched_at": self._utc_now_iso(),
                    "proposal": proposal,
                }
                producer.send(topic, value=json.dumps(message, ensure_ascii=False).encode("utf-8"))

                pushed_items.append(
                    ProposalListItem(
                        proposal_id=proposal_id,
                        space_id=sid,
                        author=proposal.get("author"),
                        title=str(proposal.get("title", "")),
                        state=str(proposal.get("state", "")),
                    )
                )

            if pushed_items:
                producer.flush()
        finally:
            producer.close()

        return DynamicSynchronousProposalResponse(proposals=pushed_items)
