from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    connections,
    utility,
)


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from configs.milvus_config import load_milvus_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize Milvus collection for SnapshotProposalVector."
    )
    parser.add_argument(
        "--dim",
        type=int,
        default=int(os.getenv("EMBEDDING_DIM", "384")),
        help="Vector dimension for `vector` and `keyword_vector` fields (default: 384).",
    )
    parser.add_argument(
        "--drop-if-exists",
        action="store_true",
        help="Drop collection first when it already exists.",
    )
    return parser.parse_args()


def connect_milvus() -> tuple[str, str]:
    config = load_milvus_config()
    alias = "default"

    connect_kwargs: dict[str, str] = {
        "alias": alias,
        "uri": config.uri,
    }
    if config.token:
        connect_kwargs["token"] = config.token

    connections.connect(**connect_kwargs)
    return alias, config.collection_proposals


def build_schema(dim: int) -> CollectionSchema:
    fields = [
        FieldSchema(
            name="proposal_id",
            dtype=DataType.VARCHAR,
            is_primary=True,
            auto_id=False,
            max_length=128,
        ),
        FieldSchema(
            name="space_id",
            dtype=DataType.VARCHAR,
            max_length=128,
        ),
        FieldSchema(
            name="vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=dim,
        ),
        FieldSchema(
            name="keyword_vector",
            dtype=DataType.FLOAT_VECTOR,
            dim=dim,
        ),
    ]
    return CollectionSchema(
        fields=fields,
        description="Snapshot proposal vectors (text + keyword vectors)",
        enable_dynamic_field=False,
    )


def create_collection(collection_name: str, dim: int, drop_if_exists: bool, alias: str) -> None:
    if utility.has_collection(collection_name, using=alias):
        if not drop_if_exists:
            print(f"Collection already exists: {collection_name}")
            return

        print(f"Dropping existing collection: {collection_name}")
        utility.drop_collection(collection_name, using=alias)

    schema = build_schema(dim=dim)
    collection = Collection(name=collection_name, schema=schema, using=alias)

    index_params = {
        "metric_type": "COSINE",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 1024},
    }
    collection.create_index(field_name="vector", index_params=index_params)
    collection.create_index(field_name="keyword_vector", index_params=index_params)
    collection.flush()

    print(f"Collection created: {collection_name}")
    print(f"Vector dimension: {dim}")
    print("Indexes created: vector, keyword_vector")


def main() -> None:
    args = parse_args()
    if args.dim <= 0:
        raise ValueError("--dim must be a positive integer")

    alias, collection_name = connect_milvus()
    try:
        create_collection(
            collection_name=collection_name,
            dim=args.dim,
            drop_if_exists=args.drop_if_exists,
            alias=alias,
        )
    finally:
        connections.disconnect(alias=alias)


if __name__ == "__main__":
    main()
