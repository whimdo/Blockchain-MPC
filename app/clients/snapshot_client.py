from __future__ import annotations

from typing import Any
import requests

from app.utils.logging_config import get_logger
from configs.provider_config import load_provider_config


class SnapshotClient:
    """Snapshot Hub GraphQL client."""

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

    def get_space_proposals(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
    ) -> list[dict[str, Any]]:
        """
        根据 space 拉取 proposals。
        """
        query = """
        query Proposals($space: String!, $first: Int!, $skip: Int!) {
            proposals(
                first: $first,
                skip: $skip,
                where: { space: $space },
                orderBy: "created",
                orderDirection: desc
            ) {
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
            }
        }
        """

        variables = {
            "space": space_id,
            "first": first,
            "skip": skip,
        }

        data = self._post_graphql(query, variables)
        proposals = data.get("proposals", [])

        self.logger.info(
            "Fetched Snapshot proposals space=%s count=%s skip=%s",
            space_id,
            len(proposals),
            skip,
        )
        return proposals