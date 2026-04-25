from __future__ import annotations

import json
import os
import threading
from dataclasses import fields
from typing import Any, Mapping

from app.clients.kafka_client import KafkaClient
from app.models.snapshot_models import SnapshotProposal
from app.services.snapshot_service import SnapshotService
from app.storage.snapshot_storage import SnapshotStorage
from app.utils.logging_config import get_logger
from configs.kafka_config import load_kafka_config
from configs.snapshot_config import load_snapshot_config


class ProposalsVectorizedAndStoreModule:
    """Consume Snapshot proposal messages, vectorize them, then store to MongoDB and Milvus."""

    def __init__(self) -> None:
        self.logger = get_logger("app.modules.proposals_vectorized_and_store")
        self.kafka_config = load_kafka_config()
        self.kafka_client = KafkaClient()
        self.snapshot_config = load_snapshot_config()
        self.snapshot_service = SnapshotService()
        self.snapshot_storage = SnapshotStorage()

        model_fields = {f.name for f in fields(SnapshotProposal)}
        self._proposal_model_fields = model_fields

    @staticmethod
    def _decode_message_value(value: Any) -> dict[str, Any]:
        """Decode Kafka message value into dict payload."""
        if isinstance(value, bytes):
            text = value.decode("utf-8")
            payload = json.loads(text)
        elif isinstance(value, str):
            payload = json.loads(value)
        elif isinstance(value, Mapping):
            payload = dict(value)
        else:
            raise ValueError(f"Unsupported message value type: {type(value)}")

        if not isinstance(payload, dict):
            raise ValueError("Message payload must be a JSON object")
        return payload

    def _build_proposal_from_payload(self, payload: dict[str, Any]) -> SnapshotProposal:
        """
        Build SnapshotProposal from message payload.

        Supported payload examples:
        1) Raw snapshot proposal (contains `id` + `space`)
        2) Normalized proposal (contains `proposal_id` + `space_id`)
        3) Wrapped payload under `proposal` or `payload` field
        """
        source_space_id = str(payload.get("space_id") or "").strip()
        if "proposal" in payload and isinstance(payload["proposal"], Mapping):
            payload = dict(payload["proposal"])
        elif "payload" in payload and isinstance(payload["payload"], Mapping):
            payload = dict(payload["payload"])

        if "proposal_id" in payload and "space_id" in payload:
            filtered = {
                key: payload[key]
                for key in payload
                if key in self._proposal_model_fields
            }
            return SnapshotProposal(**filtered)

        if "id" in payload and "space" in payload:
            return self.snapshot_service.normalize_proposal(
                payload,
                source_space_id=source_space_id or None,
            )

        raise ValueError("Payload cannot be converted to SnapshotProposal")

    def _process_one_message(self, message_value: Any) -> None:
        """Parse one Kafka message, vectorize proposal, and persist both records."""
        self.logger.info("Processing message value: %s", message_value)
        payload = self._decode_message_value(message_value)
        proposal = self._build_proposal_from_payload(payload)
        if proposal.keywords == []:
            self.logger.info(
                "Skip low-quality proposal proposal_id=%s space_id=%s",
                proposal.proposal_id,
                proposal.space_id,
            )
            self.snapshot_storage.save_snapshot_proposal(proposal)
            return
        
        vector = self.snapshot_service.get_proposal_vector(proposal)
        if vector is None:
            raise RuntimeError(f"Failed to build vector proposal_id={proposal.proposal_id}")

        self.snapshot_storage.save_snapshot_proposal(proposal)
        self.snapshot_storage.save_snapshot_proposal_vector(vector)

        self.logger.info(
            "Processed proposal proposal_id=%s space_id=%s",
            proposal.proposal_id,
            proposal.space_id,
        )

    def _consumer_loop(self, worker_index: int, group_id: str) -> None:
        """Run one Kafka consumer loop."""
        topic = self.kafka_config.topic_dao_to_vector
        consumer = self.kafka_client.consumer(
            topic=topic,
            group_id=group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )

        self.logger.info(
            "Consumer started worker=%s topic=%s group_id=%s",
            worker_index,
            topic,
            group_id,
        )

        try:
            for message in consumer:
                try:
                    self._process_one_message(message.value)
                    self.logger.info("Message processed successfully worker=%s partition=%s offset=%s", worker_index, getattr(message, "partition", "unknown"), getattr(message, "offset", "unknown"))
                    consumer.commit()
                except Exception:
                    # Commit even on bad messages to avoid poison message blocking the pipeline.
                    self.logger.exception(
                        "Message process failed worker=%s partition=%s offset=%s",
                        worker_index,
                        getattr(message, "partition", "unknown"),
                        getattr(message, "offset", "unknown"),
                    )
                    consumer.commit()
        finally:
            consumer.close()

    def run(self, consumer_count: int | None = None) -> None:
        """Start one or more consumers and block forever."""
        count = consumer_count or int(os.getenv("KAFKA_VECTOR_CONSUMER_COUNT", "1"))
        if count <= 0:
            raise ValueError("consumer_count must be > 0")

        topic = self.kafka_config.topic_dao_to_vector
        group_id = self.kafka_config.group_id
        self.logger.info(
            "Starting proposals vectorized+store module topic=%s group_id=%s consumers=%s",
            topic,
            group_id,
            count,
        )

        if count == 1:
            self.logger.info("Running consumer once in main thread")
            self._consumer_loop(worker_index=1, group_id=group_id)
            return

        threads: list[threading.Thread] = []
        for idx in range(count):
            thread = threading.Thread(
                target=self._consumer_loop,
                kwargs={"worker_index": idx + 1, "group_id": group_id},
                name=f"proposal-vector-consumer-{idx + 1}",
                daemon=False,
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


def main() -> None:
    module = ProposalsVectorizedAndStoreModule()
    module.run()


if __name__ == "__main__":
    main()
