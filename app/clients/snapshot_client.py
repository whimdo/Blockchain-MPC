from __future__ import annotations

import re
from typing import Any, Literal

import requests

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class SnapshotClient:
    """Snapshot Hub GraphQL client."""

    _DETAIL_FIELDS: dict[str, str] = {
        "summary": """
            id
            title
            state
            created
            start
            end
            scores_total
            space {
                id
                name
            }
        """,
        "standard": """
            id
            title
            author
            state
            start
            end
            snapshot
            choices
            scores
            scores_total
            created
            link
            space {
                id
                name
            }
        """,
        "full": """
            id
            title
            body
            discussion
            author
            state
            start
            end
            snapshot
            choices
            scores
            scores_total
            scores_updated
            created
            link
            space {
                id
                name
            }
        """,
    }

    def __init__(self) -> None:
        self.logger = get_logger("app.clients.snapshot_client")
        config = load_provider_config()
        self.base_url = config.snapshot_graphql_url

    def _post_graphql(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        try:
            self.logger.info("Snapshot GraphQL request start variables=%s", variables)
            response = requests.post(
                self.base_url,
                json={"query": query, "variables": variables},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                self.logger.error("Snapshot GraphQL errors=%s", data["errors"])
                raise RuntimeError(f"Snapshot GraphQL error: {data['errors']}")

            self.logger.info("Snapshot GraphQL request success")
            return data.get("data", {})
        except Exception:
            self.logger.exception("Snapshot GraphQL request failed")
            raise

    @classmethod
    def _resolve_fields(
        cls,
        detail_level: Literal["summary", "standard", "full"],
    ) -> str:
        return cls._DETAIL_FIELDS.get(detail_level, cls._DETAIL_FIELDS["full"])

    @staticmethod
    def _match_keywords(
        text: str,
        keywords: list[str],
        precision: Literal["low", "medium", "high"],
    ) -> bool:
        if not keywords:
            return True

        text_lower = text.lower()
        normalized_keywords = [item.strip().lower() for item in keywords if item.strip()]
        if not normalized_keywords:
            return True

        if precision == "low":
            return any(item in text_lower for item in normalized_keywords)

        if precision == "medium":
            return all(item in text_lower for item in normalized_keywords)

        # high: whole-word/phrase match for higher precision.
        for keyword in normalized_keywords:
            if " " in keyword:
                if keyword not in text_lower:
                    return False
                continue
            if not re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                return False
        return True

    def get_proposals_by_space(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch proposals by DAO space, with optional state pre-filter.
        """
        fields = self._resolve_fields(detail_level)
        query = """
        query Proposals($where: ProposalWhere!, $first: Int!, $skip: Int!) {
            proposals(
                first: $first,
                skip: $skip,
                where: $where,
                orderBy: "created",
                orderDirection: desc
            ) {
                __FIELDS__
            }
        }
        """
        query = query.replace("__FIELDS__", fields)

        where: dict[str, Any] = {"space": space_id}
        if state:
            where["state"] = state

        variables = {
            "where": where,
            "first": first,
            "skip": skip,
        }

        data = self._post_graphql(query, variables)
        proposals = data.get("proposals", [])

        self.logger.info(
            "Fetched Snapshot proposals space=%s count=%s skip=%s state=%s detail=%s",
            space_id,
            len(proposals),
            skip,
            state,
            detail_level,
        )
        return proposals

    def get_proposals_by_space_and_state(
        self,
        space_id: str,
        state: str,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
    ) -> list[dict[str, Any]]:
        return self.get_proposals_by_space(
            space_id=space_id,
            first=first,
            skip=skip,
            detail_level=detail_level,
            state=state,
        )

    def get_active_proposals_by_space(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
    ) -> list[dict[str, Any]]:
        return self.get_proposals_by_space_and_state(
            space_id=space_id,
            state="active",
            first=first,
            skip=skip,
            detail_level=detail_level,
        )

    def get_closed_proposals_by_space(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
    ) -> list[dict[str, Any]]:
        return self.get_proposals_by_space_and_state(
            space_id=space_id,
            state="closed",
            first=first,
            skip=skip,
            detail_level=detail_level,
        )

    def get_proposals_by_space_and_ids(
        self,
        space_id: str,
        proposal_ids: list[str],
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
    ) -> list[dict[str, Any]]:
        id_set = {item for item in proposal_ids if item}
        if not id_set:
            return []

        proposals = self.get_proposals_by_space(
            space_id=space_id,
            first=max(first, len(id_set)),
            skip=skip,
            detail_level=detail_level,
        )
        return [item for item in proposals if item.get("id") in id_set][:first]

    def get_proposals_by_space_and_time_range(
        self,
        space_id: str,
        created_from: int | None = None,
        created_to: int | None = None,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
    ) -> list[dict[str, Any]]:
        proposals = self.get_proposals_by_space(
            space_id=space_id,
            first=first,
            skip=skip,
            detail_level=detail_level,
        )

        def _in_range(created: int | None) -> bool:
            if created is None:
                return False
            if created_from is not None and created < created_from:
                return False
            if created_to is not None and created > created_to:
                return False
            return True

        return [item for item in proposals if _in_range(item.get("created"))]

    def get_precise_proposals_by_space_and_filters(
        self,
        space_id: str,
        proposal_ids: list[str] | None = None,
        states: list[str] | None = None,
        keywords: list[str] | None = None,
        created_from: int | None = None,
        created_to: int | None = None,
        min_scores_total: float | None = None,
        first: int = 20,
        skip: int = 0,
        detail_level: Literal["summary", "standard", "full"] = "full",
        precision: Literal["low", "medium", "high"] = "high",
        scan_batch_size: int = 100,
        max_scan: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        High-precision combined filtering for DAO proposals.
        """
        id_set = {item for item in (proposal_ids or []) if item}
        state_set = {item.lower() for item in (states or []) if item}
        keyword_list = keywords or []

        results: list[dict[str, Any]] = []
        scanned = 0
        current_skip = skip

        while scanned < max_scan and len(results) < first:
            page_size = min(scan_batch_size, max_scan - scanned)
            if page_size <= 0:
                break

            page = self.get_proposals_by_space(
                space_id=space_id,
                first=page_size,
                skip=current_skip,
                detail_level=detail_level,
            )
            if not page:
                break

            scanned += len(page)
            current_skip += len(page)

            for item in page:
                proposal_id = item.get("id", "")
                state = (item.get("state") or "").lower()
                created = item.get("created")
                scores_total = item.get("scores_total")
                search_text = " ".join(
                    [
                        item.get("title", "") or "",
                        item.get("body", "") or "",
                        item.get("discussion", "") or "",
                    ]
                )

                if id_set and proposal_id not in id_set:
                    continue
                if state_set and state not in state_set:
                    continue
                if created_from is not None and (created is None or created < created_from):
                    continue
                if created_to is not None and (created is None or created > created_to):
                    continue
                if min_scores_total is not None and (
                    scores_total is None or float(scores_total) < min_scores_total
                ):
                    continue
                if not self._match_keywords(search_text, keyword_list, precision):
                    continue

                results.append(item)
                if len(results) >= first:
                    break

            if len(page) < page_size:
                break

        self.logger.info(
            "Precise proposal query finished space=%s matched=%s scanned=%s",
            space_id,
            len(results),
            scanned,
        )
        return results

    def get_space_proposals(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Backward compatible wrapper.
        """
        return self.get_proposals_by_space(
            space_id=space_id,
            first=first,
            skip=skip,
            detail_level="full",
        )