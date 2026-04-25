from __future__ import annotations

import json
import os
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from app.clients.kafka_client import KafkaClient
from app.clients.snapshot_client import SnapshotClient
from app.services.snapshot_service import SnapshotService
from app.utils.logging_config import get_logger
from configs.kafka_config import load_kafka_config
from configs.snapshot_config import load_snapshot_config    

class ProposalsGetAndPushModule:
    """
    Poll Snapshot API continuously, fetch DAO proposals,
    and push proposals to Kafka topic_dao_to_vector.
    """

    def __init__(self) -> None:
        self.logger = get_logger("app.modules.proposals_get_and_push")
        self.kafka_config = load_kafka_config()
        self.snapshot_config = load_snapshot_config()
        self.kafka_client = KafkaClient()
        self.snapshot_client = SnapshotClient()

        self.space_ids = self.snapshot_config.space_ids
        self.fetch_first = self.snapshot_config.fetch_first
        self.fetch_state = self.snapshot_config.fetch_state
        self.detail_level = self.snapshot_config.fetch_detail_level
        self.poll_interval_seconds = self.snapshot_config.poll_interval_seconds
        self.max_seen_ids = self.snapshot_config.max_seen_ids

        self._seen_ids: set[str] = set()
        self._seen_queue: deque[str] = deque()
        self._validate_spaces()

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _load_space_ids() -> list[str]:
        raw = (os.getenv("SNAPSHOT_SPACE_IDS", "") or "").strip()
        ids = [item.strip() for item in raw.split(",") if item.strip()]
        if not ids:
            raise ValueError("SNAPSHOT_SPACE_IDS is required, e.g. 'aave.eth,uniswap'")
        return ids

    def _mark_seen(self, proposal_id: str) -> None:
        if proposal_id in self._seen_ids:
            return
        self._seen_ids.add(proposal_id)
        self._seen_queue.append(proposal_id)

        while len(self._seen_queue) > self.max_seen_ids:
            old = self._seen_queue.popleft()
            self._seen_ids.discard(old)

    def _build_message(self, proposal: dict[str, Any], space_id: str) -> dict[str, Any]:
        proposal_payload = dict(proposal)
        proposal_payload["source_space_id"] = space_id
        return {
            "source": "snapshot",
            "space_id": space_id,
            "fetched_at": self._utc_now_iso(),
            "proposal": proposal_payload,
        }

    def _validate_spaces(self) -> None:
        for space_id in self.space_ids:
            query_space_id = SnapshotService.to_valid_snapshot_space_id(space_id)
            try:
                space = self.snapshot_client.get_space_by_id(query_space_id)
            except Exception:
                self.logger.exception(
                    "Snapshot space validation failed space=%s query_space=%s",
                    space_id,
                    query_space_id,
                )
                continue

            if not space:
                self.logger.warning(
                    "Snapshot space not found space=%s query_space=%s. Check SNAPSHOT_SPACE_IDS.",
                    space_id,
                    query_space_id,
                )
                continue

            self.logger.info(
                "Snapshot space validated space=%s query_space=%s name=%s",
                space_id,
                space.get("id"),
                space.get("name"),
            )

    def _fetch_space_proposals(self, space_id: str) -> list[dict[str, Any]]:
        query_space_id = SnapshotService.to_valid_snapshot_space_id(space_id)
        return self.snapshot_client.get_proposals_by_space(
            space_id=query_space_id,
            first=self.fetch_first,
            skip=0,
            detail_level=self.detail_level,
            state=self.fetch_state,
        )

    def _push_space_proposals(self, producer: Any, space_id: str) -> int:
        proposals = self._fetch_space_proposals(space_id)
        output_topic = self.kafka_config.topic_dao_to_vector

        # keep chronological push order for downstream consistency
        proposals_sorted = sorted(
            proposals,
            key=lambda x: int(x.get("created") or 0),
        )

        pushed = 0
        for proposal in proposals_sorted:
            proposal_id = str(proposal.get("id", "")).strip()
            if not proposal_id:
                continue
            if proposal_id in self._seen_ids:
                continue

            message = self._build_message(proposal=proposal, space_id=space_id)
            producer.send(
                output_topic,
                value=json.dumps(message, ensure_ascii=False).encode("utf-8"),
            )
            self._mark_seen(proposal_id)
            pushed += 1

        if pushed > 0:
            producer.flush()

        self.logger.info(
            "Snapshot fetch and push done space=%s fetched=%s pushed=%s topic=%s",
            space_id,
            len(proposals),
            pushed,
            output_topic,
        )
        return pushed

    def run(self) -> None:
        """Run polling loop forever."""
        producer = self.kafka_client.producer()
        self.logger.info(
            "Starting proposals-get-and-push spaces=%s topic=%s interval=%ss first=%s state=%s detail=%s",
            self.space_ids,
            self.kafka_config.topic_dao_to_vector,
            self.poll_interval_seconds,
            self.fetch_first,
            self.fetch_state,
            self.detail_level,
        )

        try:
            while True:
                total_pushed = 0
                for space_id in self.space_ids:
                    try:
                        total_pushed += self._push_space_proposals(producer, space_id)
                    except Exception:
                        self.logger.exception("Fetch/push failed for space=%s", space_id)

                self.logger.info(
                    "Polling round finished total_pushed=%s sleep=%ss",
                    total_pushed,
                    self.poll_interval_seconds,
                )
                time.sleep(self.poll_interval_seconds)
        finally:
            producer.close()


def main() -> None:
    module = ProposalsGetAndPushModule()
    module.run()


if __name__ == "__main__":
    main()
