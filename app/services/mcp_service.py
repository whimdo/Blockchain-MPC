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


@mcp.tool()
def get_token_detail(symbol: str, include_chart: bool = True, chart_range: str = "7d") -> dict[str, Any]:
    """
    Function: Get token profile, current market detail, and optional recent chart data.
    Input: symbol, include_chart=true, chart_range="7d".
    Output: {ok, source, data.info, data.chart}; on failure {ok:false, code, message}.
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
        return ok(result, source=["binance", "mongo"])
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
    Output: {ok, source, data.klines, data.summary}; on failure {ok:false, code, message}.
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
        return ok(result, source=["binance"])
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
    Output: {ok, source, data.dao_count, data.daos}; on failure {ok:false, code, message}.
    """
    try:
        result = dao_proposal_service().get_dao_overview()
        return ok(result, source=["mongo", "config"])
    except Exception as exc:
        logger.exception("MCP get_dao_spaces failed")
        return fail("DAO_OVERVIEW_ERROR", str(exc))


@mcp.tool()
def list_proposals(space_id: str, page: int = 1, page_size: int = 5) -> dict[str, Any]:
    """
    Function: List proposals in a supported Snapshot DAO space.
    Input: space_id, page=1, page_size=5.
    Output: {ok, source, data.dao_name, data.proposals}; on failure {ok:false, code, message}.
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
        return ok(result, source=["mongo"])
    except Exception as exc:
        logger.exception("MCP list_proposals failed space_id=%s", space_id)
        return fail("DAO_PROPOSALS_ERROR", str(exc))


@mcp.tool()
def get_proposal_detail(proposal_id: str, top_k: int = 5) -> dict[str, Any]:
    """
    Function: Get proposal detail and related similar proposals.
    Input: proposal_id, top_k=5.
    Output: {ok, source, data.proposal, data.similar_proposals}; on failure {ok:false, code, message}.
    """
    try:
        normalized_proposal_id = (proposal_id or "").strip()
        if not normalized_proposal_id:
            return fail("PROPOSAL_ID_REQUIRED", "Field 'proposal_id' is required.")

        result = dao_proposal_service().get_proposal_detail_and_similar(
            proposal_id=normalized_proposal_id,
            top_k=min(20, max(1, int(top_k or 5))),
        )
        return ok(result, source=["mongo", "milvus"])
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
