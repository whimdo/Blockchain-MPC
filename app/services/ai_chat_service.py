from __future__ import annotations

from typing import Any

from app.clients.mcp_client import MCPClient, MCPQueryResult, MCPToolCallLog
from app.models.ai_assistant_models import (
    AIChatContext,
    AIChatMessage,
    AIChatRequest,
    AIChatResponse,
    AIContextDao,
    AIContextProposal,
    AIContextToken,
    AIResultCard,
    AISuggestedQuestion,
    AIToolCallRecord,
)
from app.services.ai_chat_session_service import AIChatSessionService
from app.services.ai_intent_service import AIIntentService
from app.utils.logging_config import get_logger


class AIChatServiceError(Exception):
    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class AIChatService:
    """AI chat orchestrator backed by MCP tool calls."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.ai_chat_service")
        self.session_service = AIChatSessionService()
        self.intent_service = AIIntentService()

    async def chat(self, request: AIChatRequest) -> AIChatResponse:
        session = self._get_or_create_session(request)
        user_message = AIChatMessage(role="user", content=request.message, mode=request.mode)
        self.session_service.append_message(session.session_id, user_message)

        intent = self.intent_service.detect_intent(request.message, request.mode)
        context = AIChatContext()
        result_cards: list[AIResultCard] = []
        error_message = None

        try:
            mcp_result = await self._run_mcp_query(
                question=request.message,
                intent_mode=intent.mode,
                intent_entities=intent.entities,
                required_tools=intent.required_tools,
            )
            answer = mcp_result.answer or self._fallback_answer()
            status = "success"
        except Exception as exc:
            self.logger.exception("MCP-backed AI chat failed session_id=%s", session.session_id)
            mcp_result = MCPQueryResult(answer="", tool_calls=[])
            answer = "AI assistant failed to process this request with MCP tools. Please try again later."
            status = "error"
            error_message = str(exc)

        used_tools = self._to_tool_records(mcp_result.tool_calls)
        self._build_context_and_cards(mcp_result.tool_calls, context, result_cards)

        persisted_tools = self.session_service.append_tool_calls(session.session_id, used_tools)
        assistant_message = AIChatMessage(
            role="assistant",
            content=answer,
            mode=intent.mode,
            tool_call_ids=[item.tool_call_id for item in persisted_tools if item.tool_call_id],
            metadata={
                "intent": intent.model_dump(mode="python"),
                "mcp_messages": mcp_result.messages,
                "status": status,
            },
        )
        self.session_service.append_message(session.session_id, assistant_message)
        self.session_service.update_context(session.session_id, context)

        suggested_questions = self._suggest_questions(intent.mode, context)
        self.session_service.update_suggested_questions(session.session_id, suggested_questions)

        return AIChatResponse(
            session_id=session.session_id,
            answer=answer,
            mode=intent.mode,
            status=status,
            used_tools=persisted_tools,
            context=context,
            result_cards=result_cards,
            suggested_questions=suggested_questions,
            error_message=error_message,
        )

    def _get_or_create_session(self, request: AIChatRequest):
        if request.session_id:
            return self.session_service.require_session(request.session_id)
        return self.session_service.create_session(
            title=self._build_title(request.message),
            mode=request.mode,
            user_id=request.user_id,
            client=request.client,
        )

    async def _run_mcp_query(
        self,
        *,
        question: str,
        intent_mode: str,
        intent_entities: dict[str, Any],
        required_tools: list[str],
    ) -> MCPQueryResult:
        client = MCPClient()
        try:
            await client.connect_to_server(client.server_path)
            prompt = self._build_mcp_prompt(
                question=question,
                intent_mode=intent_mode,
                intent_entities=intent_entities,
                required_tools=required_tools,
            )
            return await client.process_query_detailed(prompt)
        finally:
            await client.cleanup()

    @staticmethod
    def _build_mcp_prompt(
        *,
        question: str,
        intent_mode: str,
        intent_entities: dict[str, Any],
        required_tools: list[str],
    ) -> str:
        return (
            "You are the AI assistant for a blockchain dashboard. "
            "Answer in Chinese. Use MCP tools when data is needed, and do not invent data.\n"
            f"User question: {question}\n"
            f"Detected mode: {intent_mode}\n"
            f"Detected entities: {intent_entities}\n"
            f"Recommended tools: {required_tools}\n"
            "When you use tool results, summarize the useful facts and mention that the data comes from platform tools."
        )

    @staticmethod
    def _build_title(message: str) -> str:
        title = " ".join((message or "").strip().split())
        return title[:30] if title else "New AI Chat"

    @staticmethod
    def _fallback_answer() -> str:
        return "I could not identify enough data to answer. Please ask about a token, DAO, or proposal id."

    @staticmethod
    def _to_tool_records(tool_logs: list[MCPToolCallLog]) -> list[AIToolCallRecord]:
        records: list[AIToolCallRecord] = []
        for item in tool_logs:
            parsed = item.parsed_result if isinstance(item.parsed_result, dict) else {}
            records.append(
                AIToolCallRecord(
                    tool_call_id=item.tool_call_id,
                    tool_name=item.tool_name,
                    description="MCP tool call",
                    input=item.arguments,
                    status="success" if item.status == "success" and parsed.get("ok", True) else "failed",
                    duration_ms=item.duration_ms,
                    data_source=list(parsed.get("source") or []),
                    error_message=item.error_message or parsed.get("message"),
                    result_summary=AIChatService._tool_result_summary(item),
                    metadata={
                        "mcp": True,
                        "raw_result": item.result_text,
                        "parsed_result": item.parsed_result,
                    },
                )
            )
        return records

    @staticmethod
    def _tool_result_summary(item: MCPToolCallLog) -> str:
        parsed = item.parsed_result
        if isinstance(parsed, dict):
            if not parsed.get("ok", True):
                return str(parsed.get("message") or "MCP tool failed.")
            data = parsed.get("data")
            if isinstance(data, dict):
                return f"Returned data fields: {', '.join(list(data.keys())[:8])}."
            return "Returned MCP data."
        return "Returned MCP text result."

    def _build_context_and_cards(
        self,
        tool_logs: list[MCPToolCallLog],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        for item in tool_logs:
            parsed = item.parsed_result
            if not isinstance(parsed, dict) or not parsed.get("ok"):
                continue
            data = parsed.get("data") or {}
            source = list(parsed.get("source") or [])

            if item.tool_name == "get_token_detail":
                self._add_token_detail(data, source, context, result_cards)
            elif item.tool_name == "get_token_chart":
                self._add_token_chart(data, source, context, result_cards)
            elif item.tool_name == "get_dao_spaces":
                self._add_dao_spaces(data, source, context, result_cards)
            elif item.tool_name == "list_proposals":
                self._add_proposal_list(data, source, context, result_cards)
            elif item.tool_name == "get_proposal_detail":
                self._add_proposal_detail(data, source, context, result_cards)
            elif item.tool_name == "search_similar_proposals":
                self._add_similar_proposals(data, source, context, result_cards)

    @staticmethod
    def _add_token_detail(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        info = data.get("info") or {}
        chart = data.get("chart") or {}
        summary = chart.get("summary") or {}
        symbol = str(info.get("symbol") or chart.get("symbol") or "")
        if not symbol:
            return
        context.tokens.append(
            AIContextToken(
                symbol=symbol,
                name=info.get("name"),
                price_display=info.get("price_display"),
                change_percent=summary.get("change_percent") or info.get("price_change_24h"),
                chart_range=chart.get("range"),
                source=source,
            )
        )
        result_cards.append(
            AIResultCard(
                card_type="token",
                title=str(info.get("display_name") or symbol),
                subtitle=info.get("price_display"),
                payload=data,
                action_label="View detail",
                action_value=symbol,
            )
        )

    @staticmethod
    def _add_token_chart(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        symbol = str(data.get("symbol") or "")
        summary = data.get("summary") or {}
        if not symbol:
            return
        context.tokens.append(
            AIContextToken(
                symbol=symbol,
                change_percent=summary.get("change_percent"),
                chart_range=data.get("range"),
                source=source,
            )
        )
        result_cards.append(
            AIResultCard(
                card_type="token",
                title=f"{symbol} chart",
                subtitle=data.get("range"),
                payload=data,
                action_label="View chart",
                action_value=symbol,
            )
        )

    @staticmethod
    def _add_dao_spaces(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        for dao in data.get("daos") or []:
            context.daos.append(
                AIContextDao(
                    space_id=str(dao.get("space_id") or ""),
                    name=dao.get("name"),
                    proposal_count=dao.get("synchronized_proposals_count"),
                    source=source,
                )
            )
            result_cards.append(
                AIResultCard(
                    card_type="dao",
                    title=str(dao.get("name") or dao.get("space_id") or "DAO"),
                    subtitle=dao.get("space_id"),
                    payload=dao,
                    action_label="View proposals",
                    action_value=dao.get("space_id"),
                )
            )

    @staticmethod
    def _add_proposal_list(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        if data.get("space_id"):
            context.daos.append(
                AIContextDao(
                    space_id=str(data.get("space_id")),
                    name=data.get("dao_name"),
                    proposal_count=len(data.get("proposals") or []),
                    source=source,
                )
            )
        for proposal in data.get("proposals") or []:
            AIChatService._append_proposal(proposal, source, context, result_cards)

    @staticmethod
    def _add_proposal_detail(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        proposal = data.get("proposal") or {}
        if proposal:
            AIChatService._append_proposal(proposal, source, context, result_cards)
        similar = data.get("similar_proposals") or {}
        for item in similar.get("similar_proposals") or []:
            AIChatService._append_proposal(item, source, context, result_cards)

    @staticmethod
    def _add_similar_proposals(
        data: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        similar = data.get("similar_proposals") or {}
        for item in similar.get("similar_proposals") or []:
            AIChatService._append_proposal(item, source, context, result_cards)

    @staticmethod
    def _append_proposal(
        proposal: dict[str, Any],
        source: list[str],
        context: AIChatContext,
        result_cards: list[AIResultCard],
    ) -> None:
        proposal_id = str(proposal.get("proposal_id") or proposal.get("_id") or "")
        if not proposal_id:
            return
        context.proposals.append(
            AIContextProposal(
                proposal_id=proposal_id,
                title=proposal.get("title"),
                space_id=proposal.get("space_id"),
                state=proposal.get("state"),
                author=proposal.get("author"),
                keywords=list(proposal.get("keywords") or []),
                source=source,
            )
        )
        result_cards.append(
            AIResultCard(
                card_type="proposal",
                title=str(proposal.get("title") or proposal_id),
                subtitle=f"{proposal.get('space_id') or ''} · {proposal.get('state') or ''}".strip(),
                payload=proposal,
                action_label="View proposal",
                action_value=proposal_id,
            )
        )

    @staticmethod
    def _suggest_questions(mode: str, context: AIChatContext) -> list[AISuggestedQuestion]:
        if mode == "token" and context.tokens:
            symbol = context.tokens[0].symbol
            return [
                AISuggestedQuestion(text=f"{symbol} 最近成交量如何？", mode="token", category="token"),
                AISuggestedQuestion(text=f"帮我总结 {symbol} 当前状态", mode="token", category="token"),
            ]
        if mode == "dao" and context.daos:
            dao = context.daos[0]
            return [
                AISuggestedQuestion(text=f"{dao.name or dao.space_id} 最近有哪些提案？", mode="dao", category="dao"),
                AISuggestedQuestion(text="当前平台支持哪些 DAO？", mode="dao", category="dao"),
            ]
        if mode == "proposal" and context.proposals:
            proposal = context.proposals[0]
            return [
                AISuggestedQuestion(text=f"查找和 {proposal.proposal_id} 相似的提案", mode="proposal", category="proposal"),
                AISuggestedQuestion(text="解释这个 Proposal 的投票结果", mode="proposal", category="proposal"),
            ]
        return [
            AISuggestedQuestion(text="BTC 最近 7 天走势如何？", mode="token", category="token"),
            AISuggestedQuestion(text="当前平台支持哪些 DAO？", mode="dao", category="dao"),
            AISuggestedQuestion(text="查找某个 Proposal 的相似提案", mode="proposal", category="proposal"),
        ]
