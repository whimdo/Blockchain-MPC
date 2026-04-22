from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.kafka_config import load_kafka_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Delete and recreate a Kafka topic (collection)."
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="",
        help="Target Kafka topic name.",
    )
    parser.add_argument(
        "--from-config",
        choices=["dao_to_vector", "vector_to_dao"],
        default="",
        help="Use topic name from kafka config.",
    )
    parser.add_argument(
        "--partitions",
        type=int,
        default=1,
        help="Partition count for the recreated topic (default: 1).",
    )
    parser.add_argument(
        "--replication-factor",
        type=int,
        default=1,
        help="Replication factor for the recreated topic (default: 1).",
    )
    parser.add_argument(
        "--config",
        action="append",
        default=[],
        help="Topic config in key=value form; can pass multiple times.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=30000,
        help="Admin operation timeout in milliseconds (default: 30000).",
    )
    parser.add_argument(
        "--wait-seconds",
        type=float,
        default=20.0,
        help="Max wait time for topic deletion before recreate (default: 20).",
    )
    return parser.parse_args()


def resolve_topic_name(args: argparse.Namespace) -> str:
    config = load_kafka_config()
    if args.topic:
        return args.topic
    if args.from_config == "dao_to_vector":
        return config.topic_dao_to_vector
    if args.from_config == "vector_to_dao":
        return config.topic_vector_to_dao
    raise ValueError("Please provide --topic or --from-config.")


def build_admin_client() -> KafkaAdminClient:
    config = load_kafka_config()
    bootstrap_servers = [
        item.strip() for item in config.bootstrap_servers.split(",") if item.strip()
    ]

    auth_kwargs: dict[str, str] = {
        "security_protocol": config.security_protocol,
    }
    if config.sasl_mechanism:
        auth_kwargs["sasl_mechanism"] = config.sasl_mechanism
    if config.sasl_username:
        auth_kwargs["sasl_plain_username"] = config.sasl_username
    if config.sasl_password:
        auth_kwargs["sasl_plain_password"] = config.sasl_password

    return KafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id="rebuild-kafka-topic-script",
        **auth_kwargs,
    )


def parse_topic_configs(raw_items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in raw_items:
        if "=" not in item:
            raise ValueError(f"Invalid --config value: {item}; expected key=value")
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise ValueError(f"Invalid --config value: {item}; key is empty")
        parsed[key] = value
    return parsed


def wait_until_topic_deleted(
    admin: KafkaAdminClient, topic: str, wait_seconds: float
) -> None:
    deadline = time.time() + wait_seconds
    while time.time() < deadline:
        if topic not in admin.list_topics():
            return
        time.sleep(0.5)

    raise TimeoutError(
        f"Topic still exists after waiting {wait_seconds}s: {topic}. "
        "Deletion may be disabled on broker or still in progress."
    )


def rebuild_topic(
    topic: str,
    partitions: int,
    replication_factor: int,
    topic_configs: dict[str, str],
    timeout_ms: int,
    wait_seconds: float,
) -> None:
    admin = build_admin_client()
    try:
        print(f"Deleting topic(collection): {topic}")
        try:
            admin.delete_topics([topic], timeout_ms=timeout_ms)
        except UnknownTopicOrPartitionError:
            print(f"Topic not found, skip delete: {topic}")

        wait_until_topic_deleted(admin=admin, topic=topic, wait_seconds=wait_seconds)

        print(f"Creating topic(collection): {topic}")
        new_topic = NewTopic(
            name=topic,
            num_partitions=partitions,
            replication_factor=replication_factor,
            topic_configs=topic_configs or None,
        )
        admin.create_topics([new_topic], timeout_ms=timeout_ms)
        print("Topic recreate succeeded.")
        print(f"partitions={partitions}, replication_factor={replication_factor}")
        if topic_configs:
            print(f"topic_configs={topic_configs}")
    except TopicAlreadyExistsError as exc:
        raise RuntimeError(
            f"Topic already exists after rebuild attempt: {topic}"
        ) from exc
    finally:
        admin.close()


def main() -> None:
    args = parse_args()
    topic = resolve_topic_name(args)
    if args.partitions <= 0:
        raise ValueError("--partitions must be a positive integer")
    if args.replication_factor <= 0:
        raise ValueError("--replication-factor must be a positive integer")
    if args.timeout_ms <= 0:
        raise ValueError("--timeout-ms must be a positive integer")
    if args.wait_seconds <= 0:
        raise ValueError("--wait-seconds must be a positive number")

    topic_configs = parse_topic_configs(args.config)
    rebuild_topic(
        topic=topic,
        partitions=args.partitions,
        replication_factor=args.replication_factor,
        topic_configs=topic_configs,
        timeout_ms=args.timeout_ms,
        wait_seconds=args.wait_seconds,
    )


if __name__ == "__main__":
    main()
