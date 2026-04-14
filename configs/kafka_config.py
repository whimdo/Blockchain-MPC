import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class KafkaConfig:
    bootstrap_servers: str
    topic_dao_to_vector: str
    topic_vector_to_dao: str
    group_id: str
    security_protocol: str
    sasl_mechanism: str
    sasl_username: str
    sasl_password: str


def load_kafka_config() -> KafkaConfig:
    """Load Kafka config from environment variables."""
    return KafkaConfig(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        topic_dao_to_vector=os.getenv("KAFKA_TOPIC_DAO_TO_VECTOR", "dao_to_vector"),
        topic_vector_to_dao=os.getenv("KAFKA_TOPIC_VECTOR_TO_DAO", "vector_to_dao"),
        group_id=os.getenv("KAFKA_GROUP_ID", "blockchain_mpc_group"),
        security_protocol=os.getenv("KAFKA_SECURITY_PROTOCOL", "PLAINTEXT"),
        sasl_mechanism=os.getenv("KAFKA_SASL_MECHANISM", ""),
        sasl_username=os.getenv("KAFKA_SASL_USERNAME", ""),
        sasl_password=os.getenv("KAFKA_SASL_PASSWORD", ""),
    )
