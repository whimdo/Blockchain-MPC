from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Mapping, Sequence

from app.clients.milvus_client import MilvusClient
from app.models.snapshot_models import SnapshotProposalVector
from app.utils.logging_config import get_logger
from configs.milvus_config import load_milvus_config


class MilvusService:
    """Service layer for basic Milvus insert/query/search operations."""

    def __init__(self) -> None:
        """初始化 Milvus 服务：加载配置、日志器以及底层 Milvus 客户端。"""
        self.logger = get_logger("app.services.milvus_service")
        self.config = load_milvus_config()
        self.client = MilvusClient()

    def _resolve_collection_name(self, collection: str | None) -> str:
        """解析 collection 名称，支持业务别名并提供默认 proposals 集合。"""
        if not collection:
            return self.config.collection_proposals

        mapping = {
            "proposals": self.config.collection_proposals,
        }
        return mapping.get(collection, collection)

    @staticmethod
    def _normalize_row(row: Mapping[str, Any] | Any) -> dict[str, Any]:
        """将输入行统一转换为 dict，支持 mapping/dataclass/to_dict 对象。"""
        if isinstance(row, Mapping):
            return dict(row)
        if is_dataclass(row):
            return asdict(row)
        if hasattr(row, "to_dict") and callable(row.to_dict):
            result = row.to_dict()
            if isinstance(result, Mapping):
                return dict(result)
        raise TypeError(f"Unsupported row type for Milvus insert: {type(row)}")

    @staticmethod
    def _serialize_hits(hits: Any) -> list[list[dict[str, Any]]]:
        """将 Milvus 原始命中结果标准化为可序列化字典结构。"""
        serialized: list[list[dict[str, Any]]] = []
        for one_query_hits in hits:
            query_result: list[dict[str, Any]] = []
            for hit in one_query_hits:
                entity_fields: dict[str, Any] = {}
                if hasattr(hit, "entity") and hit.entity is not None:
                    try:
                        entity_fields = dict(hit.entity)
                    except Exception:
                        entity_fields = {}

                query_result.append(
                    {
                        "id": hit.id,
                        "distance": float(hit.distance),
                        "score": float(hit.score) if hasattr(hit, "score") else float(hit.distance),
                        "fields": entity_fields,
                    }
                )
            serialized.append(query_result)
        return serialized

    def ping(self) -> None:
        """检查 Milvus 连接可用性。"""
        self.client.ping()

    def collection(self, collection: str | None = None):
        """获取目标 Milvus Collection 对象。"""
        name = self._resolve_collection_name(collection)
        return self.client.collection(name)

    def load(self, collection: str | None = None) -> None:
        """将指定 collection 加载到内存，供查询和检索使用。"""
        coll = self.collection(collection)
        coll.load()

    def release(self, collection: str | None = None) -> None:
        """释放指定 collection 的内存加载状态。"""
        coll = self.collection(collection)
        coll.release()

    def flush(self, collection: str | None = None) -> None:
        """将指定 collection 的写入数据持久化到存储层。"""
        coll = self.collection(collection)
        coll.flush()

    def insert_rows(
        self,
        rows: Sequence[Mapping[str, Any] | Any],
        collection: str | None = None,
        flush: bool = True,
    ) -> int:
        """
        向目标 collection 插入通用结构数据。
        支持 dict / dataclass / 实现 to_dict() 的对象。
        """
        if not rows:
            return 0

        coll = self.collection(collection)
        payload = [self._normalize_row(row) for row in rows]
        result = coll.insert(payload)

        if flush:
            coll.flush()

        inserted = len(getattr(result, "primary_keys", [])) or len(payload)
        self.logger.info(
            "Milvus insert success collection=%s rows=%s",
            coll.name,
            inserted,
        )
        return inserted

    def insert_proposal_vectors(
        self,
        items: Sequence[SnapshotProposalVector | Mapping[str, Any]],
        flush: bool = True,
    ) -> int:
        """
        将提案向量数据写入配置中的 proposals collection。
        """
        return self.insert_rows(
            rows=items,
            collection=self.config.collection_proposals,
            flush=flush,
        )

    def query(
        self,
        expr: str,
        output_fields: Sequence[str] | None = None,
        collection: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """按表达式查询 collection 数据并返回字典列表。"""
        coll = self.collection(collection)
        output = list(output_fields) if output_fields else ["*"]
        rows = coll.query(expr=expr, output_fields=output, limit=limit)
        return [dict(item) for item in rows]

    def delete_by_expr(self, expr: str, collection: str | None = None) -> dict[str, Any]:
        """按表达式删除 collection 数据，并返回删除统计信息。"""
        coll = self.collection(collection)
        result = coll.delete(expr=expr)
        self.logger.info("Milvus delete success collection=%s expr=%s", coll.name, expr)
        return {
            "delete_count": getattr(result, "delete_count", None),
            "timestamp": getattr(result, "timestamp", None),
        }

    def count(self, collection: str | None = None) -> int:
        """返回指定 collection 当前实体数量。"""
        coll = self.collection(collection)
        return int(coll.num_entities)

    def search_vectors(
        self,
        query_vectors: Sequence[Sequence[float]],
        collection: str | None = None,
        vector_field: str = "vector",
        top_k: int = 10,
        expr: str | None = None,
        output_fields: Sequence[str] | None = None,
        metric_type: str = "COSINE",
        nprobe: int = 16,
    ) -> list[list[dict[str, Any]]]:
        """
        通用向量相似检索接口，支持单/多查询向量。
        返回每个查询向量对应的标准化命中结果列表。
        """
        if not query_vectors:
            return []
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        coll = self.collection(collection)
        coll.load()

        params = {
            "metric_type": metric_type,
            "params": {"nprobe": nprobe},
        }
        output = list(output_fields) if output_fields else []
        hits = coll.search(
            data=[list(vec) for vec in query_vectors],
            anns_field=vector_field,
            param=params,
            limit=top_k,
            expr=expr,
            output_fields=output,
        )
        return self._serialize_hits(hits)

    def search_proposals_by_vector(
        self,
        query_vector: Sequence[float],
        top_k: int = 10,
        expr: str | None = None,
        output_fields: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        """在 proposals collection 的 `vector` 字段上执行相似检索。"""
        result = self.search_vectors(
            query_vectors=[query_vector],
            collection=self.config.collection_proposals,
            vector_field="vector",
            top_k=top_k,
            expr=expr,
            output_fields=output_fields,
            metric_type="COSINE",
        )
        return result[0] if result else []

    def search_proposals_by_keyword_vector(
        self,
        query_vector: Sequence[float],
        top_k: int = 10,
        expr: str | None = None,
        output_fields: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        """在 proposals collection 的 `keyword_vector` 字段上执行相似检索。"""
        result = self.search_vectors(
            query_vectors=[query_vector],
            collection=self.config.collection_proposals,
            vector_field="keyword_vector",
            top_k=top_k,
            expr=expr,
            output_fields=output_fields,
            metric_type="COSINE",
        )
        return result[0] if result else []
