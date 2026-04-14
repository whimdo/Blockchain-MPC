from __future__ import annotations

from kafka import KafkaConsumer, KafkaProducer

from app.utils.logging_config import get_logger
from configs.kafka_config import load_kafka_config


class KafkaMQClient:
    """Kafka client wrapper for shared message queue access."""

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.kafka_client")
        self.config = load_kafka_config()

    @property
    def bootstrap_servers(self) -> list[str]:
        return [
            item.strip()
            for item in self.config.bootstrap_servers.split(",")
            if item.strip()
        ]

    def _auth_kwargs(self) -> dict[str, str]:
        kwargs: dict[str, str] = {
            "security_protocol": self.config.security_protocol,
        }

        if self.config.sasl_mechanism:
            kwargs["sasl_mechanism"] = self.config.sasl_mechanism
        if self.config.sasl_username:
            kwargs["sasl_plain_username"] = self.config.sasl_username
        if self.config.sasl_password:
            kwargs["sasl_plain_password"] = self.config.sasl_password

        return kwargs

    def ping(self) -> None:
        """Check Kafka connection."""
        producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **self._auth_kwargs(),
        )
        try:
            if not producer.bootstrap_connected():
                raise RuntimeError(
                    f"Kafka bootstrap not connected: {self.bootstrap_servers}"
                )
        finally:
            producer.close()

    def producer(self) -> KafkaProducer:
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            **self._auth_kwargs(),
        )

    def consumer(
        self,
        topic: str,
        group_id: str | None = None,
    ) -> KafkaConsumer:
        return KafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id or self.config.group_id,
            **self._auth_kwargs(),
        )


KafkaClient = KafkaMQClient
