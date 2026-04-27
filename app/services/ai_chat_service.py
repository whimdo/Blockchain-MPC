from __future__ import annotations

from app.clients.mcp_client import MCPQueryResult, MCPToolCallLog
from app.models.ai_assistant_models import (
    AIChatMessage,
    AIChatRequest,
    AIChatResponse,
    AIToolCallRecord,
)
from app.services.ai_chat_session_service import AIChatSessionService
from app.services.dao_proposal_service import DaoProposalService
from app.services.dashboard_tokens_service import DashboardTokensService
from app.services.mcp_client_manager import mcp_client_manager
from app.utils.logging_config import get_logger


class AIChatServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AIChatService:
    """Simplified AI chat service backed by sessions, quick replies, and MCP fallback."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.ai_chat_service")
        self.session_service = AIChatSessionService()
        self.dao_service = DaoProposalService()
        self.dashboard_tokens_service = DashboardTokensService()

    async def chat(self, request: AIChatRequest) -> AIChatResponse:
        session = self._get_or_create_session(request)
        user_message = AIChatMessage(role="user", content=request.message, mode="auto")
        self.session_service.append_message(session.session_id, user_message)

        error_message = None
        try:
            mcp_result = self._try_quick_answer(request.message)
            if mcp_result is None:
                mcp_result = await self._run_mcp_query(request.message)
            answer = mcp_result.answer or self._fallback_answer()
            status = "success"
        except Exception as exc:
            self.logger.exception("AI chat failed session_id=%s", session.session_id)
            mcp_result = MCPQueryResult(answer="", tool_calls=[])
            answer = "AI assistant failed to process this request. Please try again later."
            status = "error"
            error_message = str(exc)

        used_tools = self._to_tool_records(mcp_result.tool_calls)
        persisted_tools = self.session_service.append_tool_calls(session.session_id, used_tools)

        assistant_message = AIChatMessage(
            role="assistant",
            content=answer,
            mode="auto",
            tool_call_ids=[item.tool_call_id for item in persisted_tools if item.tool_call_id],
        )
        self.session_service.append_message(session.session_id, assistant_message)

        return AIChatResponse(
            session_id=session.session_id,
            answer=answer,
            mode="auto",
            status=status,
            used_tools=persisted_tools,
            result_cards=[],
            error_message=error_message,
        )

    def _get_or_create_session(self, request: AIChatRequest):
        if request.session_id:
            return self.session_service.require_session(request.session_id)
        return self.session_service.create_session(
            title=self._build_title(request.message),
            mode="auto",
            user_id=request.user_id,
            client=request.client,
        )

    async def _run_mcp_query(self, question: str) -> MCPQueryResult:
        prompt = self._build_mcp_prompt(question)
        return await mcp_client_manager.process_query_detailed(prompt)

    def _try_quick_answer(self, question: str) -> MCPQueryResult | None:
        text = " ".join((question or "").strip().split())
        normalized = text.lower()
        if not normalized:
            return None

        if normalized in {"你好", "您好", "hi", "hello", "在吗"}:
            return MCPQueryResult(
                answer="你好，我是 ChainPilot 的链上智能助手。你可以问我代币行情、DAO 治理空间或 Proposal 相关问题。",
                tool_calls=[],
                messages=[],
            )

        if self._is_dao_overview_question(normalized):
            overview = self.dao_service.get_dao_overview()
            dao_names = [f"{dao.name}（{dao.space_id}）" for dao in overview.daos]
            answer = (
                f"当前平台支持 {overview.dao_count} 个 DAO：{'、'.join(dao_names)}。"
                "这些数据来自平台本地配置和 MongoDB 同步统计。"
                if dao_names
                else "当前平台暂未配置可展示的 DAO。该结果来自平台本地配置。"
            )
            return MCPQueryResult(
                answer=answer,
                tool_calls=[
                    MCPToolCallLog(
                        tool_call_id="quick_get_dao_spaces",
                        tool_name="get_dao_spaces",
                        arguments={},
                        status="success",
                        duration_ms=0,
                        parsed_result={
                            "ok": True,
                            "source": ["mongo", "config"],
                            "data": overview.model_dump(mode="python"),
                        },
                    )
                ],
                messages=[],
            )

        if self._is_token_overview_question(normalized):
            overview = self.dashboard_tokens_service.get_overview()
            symbols = [card.symbol for group in overview.groups for card in group.cards]
            answer = (
                f"当前平台支持 {overview.total_tokens} 个代币：{'、'.join(symbols)}。"
                "这些数据来自平台本地 Token 配置和行情缓存。"
            )
            return MCPQueryResult(
                answer=answer,
                tool_calls=[
                    MCPToolCallLog(
                        tool_call_id="quick_get_token_overview",
                        tool_name="get_token_overview",
                        arguments={},
                        status="success",
                        duration_ms=0,
                        parsed_result={
                            "ok": True,
                            "source": ["mongo", "config"],
                            "data": {"total_tokens": overview.total_tokens, "symbols": symbols},
                        },
                    )
                ],
                messages=[],
            )

        if any(keyword in normalized for keyword in {"chainpilot", "平台功能", "核心功能", "怎么使用", "使用流程"}):
            return MCPQueryResult(
                answer=(
                    "ChainPilot 主要提供三个能力：1. 代币总览与详情分析；"
                    "2. DAO 治理空间、Proposal 列表与详情查看；"
                    "3. AI 助手，用于基于平台工具回答链上资产和治理问题。"
                ),
                tool_calls=[],
                messages=[],
            )

        return None

    @staticmethod
    def _is_dao_overview_question(normalized: str) -> bool:
        return "dao" in normalized and any(keyword in normalized for keyword in {"支持", "哪些", "列表", "当前平台"})

    @staticmethod
    def _is_token_overview_question(normalized: str) -> bool:
        return any(keyword in normalized for keyword in {"token", "代币", "币种"}) and any(
            keyword in normalized for keyword in {"支持", "哪些", "列表", "当前平台"}
        )

    @staticmethod
    def _build_mcp_prompt(question: str) -> str:
        return (
            "You are the AI assistant for ChainPilot, a blockchain dashboard. "
            "Answer in Chinese. Use MCP tools when platform data is needed. "
            "Do not invent data. If tool results are used, mention that the data comes from platform tools.\n"
            f"User question: {question}"
        )

    @staticmethod
    def _build_title(message: str) -> str:
        title = " ".join((message or "").strip().split())
        return title[:30] if title else "New AI Chat"

    @staticmethod
    def _fallback_answer() -> str:
        return "我暂时没有足够信息回答这个问题。你可以尝试询问代币、DAO 或 Proposal 相关内容。"

    @staticmethod
    def _to_tool_records(tool_logs: list[MCPToolCallLog]) -> list[AIToolCallRecord]:
        records: list[AIToolCallRecord] = []
        for item in tool_logs:
            parsed = item.parsed_result if isinstance(item.parsed_result, dict) else {}
            records.append(
                AIToolCallRecord(
                    tool_call_id=item.tool_call_id,
                    tool_name=item.tool_name,
                    status="success" if item.status == "success" and parsed.get("ok", True) else "failed",
                )
            )
        return records
