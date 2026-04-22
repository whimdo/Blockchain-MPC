from __future__ import annotations

import argparse
import sys
from pathlib import Path

from kafka import KafkaConsumer, TopicPartition


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.kafka_config import load_kafka_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check whether a Kafka topic is empty."
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
        "--timeout-ms",
        type=int,
        default=10000,
        help="Kafka API timeout in milliseconds (default: 10000).",
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


def build_consumer() -> KafkaConsumer:
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

    return KafkaConsumer(
        bootstrap_servers=bootstrap_servers,
        enable_auto_commit=False,
        **auth_kwargs,
    )


def _fetch_offsets(
    consumer: KafkaConsumer,
    method_name: str,
    topic_partitions: list[TopicPartition],
    timeout_ms: int,
) -> dict[TopicPartition, int]:
    method = getattr(consumer, method_name)
    try:
        return method(topic_partitions, timeout_ms=timeout_ms)
    except TypeError as exc:
        # Backward compatibility for older kafka-python versions:
        # beginning_offsets/end_offsets may not accept timeout_ms.
        if "unexpected keyword argument 'timeout_ms'" not in str(exc):
            raise
        return method(topic_partitions)


def check_topic_empty(topic: str, timeout_ms: int) -> tuple[bool, int]:
    consumer = build_consumer()
    try:
        partitions = consumer.partitions_for_topic(topic)
        if partitions is None:
            raise RuntimeError(f"Topic not found or metadata unavailable: {topic}")
        if not partitions:
            # Topic exists but no partitions: treat as empty.
            return True, 0

        topic_partitions = [TopicPartition(topic, p) for p in sorted(partitions)]
        begin_offsets = _fetch_offsets(
            consumer=consumer,
            method_name="beginning_offsets",
            topic_partitions=topic_partitions,
            timeout_ms=timeout_ms,
        )
        end_offsets = _fetch_offsets(
            consumer=consumer,
            method_name="end_offsets",
            topic_partitions=topic_partitions,
            timeout_ms=timeout_ms,
        )

        total_messages = 0
        print(f"Topic: {topic}")
        for tp in topic_partitions:
            begin = begin_offsets.get(tp, 0)
            end = end_offsets.get(tp, 0)
            count = max(end - begin, 0)
            total_messages += count
            print(
                f"partition={tp.partition}, begin_offset={begin}, "
                f"end_offset={end}, approx_messages={count}"
            )

        return total_messages == 0, total_messages
    finally:
        consumer.close()


def main() -> None:
    args = parse_args()
    if args.timeout_ms <= 0:
        raise ValueError("--timeout-ms must be a positive integer")

    topic = resolve_topic_name(args)
    is_empty, total_messages = check_topic_empty(topic=topic, timeout_ms=args.timeout_ms)
    if is_empty:
        print("Result: EMPTY")
    else:
        print(f"Result: NOT EMPTY, approx_total_messages={total_messages}")


if __name__ == "__main__":
    main()
