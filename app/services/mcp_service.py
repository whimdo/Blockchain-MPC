from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.dao_proposal_service import DaoProposalService
from app.services.token_detail_service import TokenDetailService
from app.utils.logging_config import get_logger


logger = get_logger("app.services.mcp_service")
mcp = FastMCP("blockchain-mpc")

_token_detail_service: TokenDetailService | None = None
_dao_proposal_service: DaoProposalService | None = None


def token_detail_service() -> TokenDetailService:
    global _token_detail_service
    if _token_detail_service is None:
        _token_detail_service = TokenDetailService()
    return _token_detail_service


def dao_proposal_service() -> DaoProposalService:
    global _dao_proposal_service
    if _dao_proposal_service is None:
        _dao_proposal_service = DaoProposalService()
    return _dao_proposal_service


def to_plain(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, tuple):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_plain(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return to_plain(value.model_dump(mode="python"))
    if is_dataclass(value):
        return to_plain(asdict(value))
    if hasattr(value, "to_dict"):
        return to_plain(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_plain(value.__dict__)
    return str(value)


def ok(data: Any, source: list[str] | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "source": source or [],
        "data": to_plain(data),
    }


def fail(code: str, message: str) -> dict[str, Any]:
    return {
        "ok": False,
        "code": code,
        "message": message,
    }


def _pick(data: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: data.get(key) for key in keys if key in data}


def summarize_token_detail(result: Any) -> dict[str, Any]:
    plain = to_plain(result) or {}
    info = plain.get("info") or {}
    return _pick(
        info,
        [
            "symbol",
            "name",
            "display_name",
            "price_display",
            "price_change_24h",
            "high_24h",
            "low_24h",
            "volume_24h",
            "updated_at",
            "status",
        ],
    )


def summarize_token_chart(result: Any) -> dict[str, Any]:
    plain = to_plain(result) or {}
    summary = plain.get("summary") or {}
    return {
        "symbol": plain.get("symbol"),
        "price_symbol": plain.get("price_symbol"),
        "range": plain.get("range"),
        "interval": plain.get("interval"),
        "source": plain.get("source"),
        "summary": _pick(
            summary,
            [
                "start_price",
                "end_price",
                "change",
                "change_percent",
                "high",
                "low",
                "total_quote_volume",
                "total_trades",
            ],
        ),
    }


def summarize_dao_overview(result: Any) -> dict[str, Any]:
    plain = to_plain(result) or {}
    return {
        "page_updated_at": plain.get("page_updated_at"),
        "dao_count": plain.get("dao_count"),
        "daos": [
            _pick(
                dao,
                [
                    "name",
                    "space_id",
                    "description",
                    "tags",
                    "enabled",
                    "latest_synchronization_time",
                    "synchronized_proposals_count",
                ],
            )
            for dao in plain.get("daos") or []
        ],
    }


def summarize_proposal_list(result: Any, max_items: int = 8) -> dict[str, Any]:
    plain = to_plain(result) or {}
    return {
        "page_updated_at": plain.get("page_updated_at"),
        "space_id": plain.get("space_id"),
        "dao_name": plain.get("dao_name"),
        "page": plain.get("page"),
        "page_size": plain.get("page_size"),
        "total": plain.get("total"),
        "proposals": [
            _pick(item, ["proposal_id", "space_id", "author", "title", "state", "keywords"])
            for item in (plain.get("proposals") or [])[:max_items]
        ],
    }


def _brief_text(value: str | None, limit: int = 800) -> str | None:
    if not value:
        return value
    text = " ".join(str(value).split())
    return text if len(text) <= limit else f"{text[:limit]}..."


def summarize_proposal_detail(result: Any, max_similar: int = 5) -> dict[str, Any]:
    plain = to_plain(result) or {}
    proposal = plain.get("proposal") or {}
    similar = plain.get("similar_proposals") or {}
    return {
        "proposal": {
            **_pick(
                proposal,
                [
                    "proposal_id",
                    "space_id",
                    "title",
                    "author",
                    "state",
                    "choices",
                    "scores",
                    "scores_total",
                    "created",
                    "link",
                    "keywords",
                ],
            ),
            "body_brief": _brief_text(proposal.get("body")),
        },
        "similar_proposals": {
            "proposal_id": similar.get("proposal_id"),
            "space_id": similar.get("space_id"),
            "top_k": similar.get("top_k"),
            "similar_proposals": [
                _pick(item, ["proposal_id", "space_id", "author", "title", "state", "keywords"])
                for item in (similar.get("similar_proposals") or [])[:max_similar]
            ],
        },
    }


@mcp.tool()
def get_token_detail(symbol: str, include_chart: bool = False, chart_range: str = "7d") -> dict[str, Any]:
    """
    Function: Get token profile, current market detail, and optional recent chart data.
    Input: symbol, include_chart=false, chart_range="7d".
    Output: compact token market fields only; on failure {ok:false, code, message}.
    """
    try:
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            return fail("SYMBOL_REQUIRED", "Field 'symbol' is required.")

        result = token_detail_service().build_detail(
            symbol=normalized_symbol,
            include_chart=include_chart,
            chart_range=chart_range,
        )
        return ok(summarize_token_detail(result), source=["binance", "mongo"])
    except LookupError:
        return fail("TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception as exc:
        logger.exception("MCP get_token_detail failed symbol=%s", symbol)
        return fail("TOKEN_DETAIL_ERROR", str(exc))


@mcp.tool()
def get_token_chart(symbol: str, chart_range: str = "7d", interval: str | None = None) -> dict[str, Any]:
    """
    Function: Get token kline chart data and trend summary.
    Input: symbol, chart_range="7d", interval=None.
    Output: compact chart summary only, without full kline rows; on failure {ok:false, code, message}.
    """
    try:
        normalized_symbol = (symbol or "").strip().upper()
        if not normalized_symbol:
            return fail("SYMBOL_REQUIRED", "Field 'symbol' is required.")

        result = token_detail_service().build_chart(
            symbol=normalized_symbol,
            chart_range=chart_range,
            interval=interval,
        )
        return ok(summarize_token_chart(result), source=["binance"])
    except LookupError:
        return fail("TOKEN_NOT_FOUND", "Token configuration not found.")
    except Exception as exc:
        logger.exception("MCP get_token_chart failed symbol=%s", symbol)
        return fail("TOKEN_CHART_ERROR", str(exc))


@mcp.tool()
def get_dao_spaces() -> dict[str, Any]:
    """
    Function: Get the DAO spaces currently supported by this platform.
    Input: no parameters.
    Output: compact DAO overview; on failure {ok:false, code, message}.
    """
    try:
        result = dao_proposal_service().get_dao_overview()
        return ok(summarize_dao_overview(result), source=["mongo", "config"])
    except Exception as exc:
        logger.exception("MCP get_dao_spaces failed")
        return fail("DAO_OVERVIEW_ERROR", str(exc))


@mcp.tool()
def list_proposals(space_id: str, page: int = 1, page_size: int = 5) -> dict[str, Any]:
    """
    Function: List proposals in a supported Snapshot DAO space.
    Input: space_id, page=1, page_size=5.
    Output: compact proposal list; on failure {ok:false, code, message}.
    """
    try:
        normalized_space_id = (space_id or "").strip()
        if not normalized_space_id:
            return fail("SPACE_ID_REQUIRED", "Field 'space_id' is required.")

        result = dao_proposal_service().get_proposals_in_dao(
            space_id=normalized_space_id,
            page=max(1, int(page or 1)),
            page_size=min(100, max(1, int(page_size or 5))),
        )
        return ok(summarize_proposal_list(result), source=["mongo"])
    except Exception as exc:
        logger.exception("MCP list_proposals failed space_id=%s", space_id)
        return fail("DAO_PROPOSALS_ERROR", str(exc))


@mcp.tool()
def get_proposal_detail(proposal_id: str, top_k: int = 5) -> dict[str, Any]:
    """
    Function: Get proposal detail and related similar proposals.
    Input: proposal_id, top_k=5.
    Output: compact proposal detail and similar proposals; on failure {ok:false, code, message}.
    """
    try:
        normalized_proposal_id = (proposal_id or "").strip()
        if not normalized_proposal_id:
            return fail("PROPOSAL_ID_REQUIRED", "Field 'proposal_id' is required.")

        result = dao_proposal_service().get_proposal_detail_and_similar(
            proposal_id=normalized_proposal_id,
            top_k=min(20, max(1, int(top_k or 5))),
        )
        return ok(summarize_proposal_detail(result), source=["mongo", "milvus"])
    except Exception as exc:
        logger.exception("MCP get_proposal_detail failed proposal_id=%s", proposal_id)
        return fail("PROPOSAL_DETAIL_ERROR", str(exc))


@mcp.tool()
def search_similar_proposals(proposal_id: str, top_k: int = 5) -> dict[str, Any]:
    """
    Function: Search proposals semantically similar to a given proposal.
    Input: proposal_id, top_k=5.
    Output: {ok, source, data.proposal_id, data.similar_proposals}; on failure {ok:false, code, message}.
    """
    detail_result = get_proposal_detail(proposal_id=proposal_id, top_k=top_k)
    if not detail_result.get("ok"):
        return detail_result

    data = detail_result.get("data") or {}
    return ok(
        {
            "proposal_id": proposal_id,
            "similar_proposals": data.get("similar_proposals", {}),
        },
        source=["mongo", "milvus"],
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
