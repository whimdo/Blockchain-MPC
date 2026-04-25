from __future__ import annotations

import re

from app.models.ai_assistant_models import AIChatMode, AIIntentResult


class AIIntentService:
    """Rule-based intent detector for the first AI chat version."""

    TOKEN_SYMBOLS = {
        "BTC",
        "ETH",
        "DOGE",
        "AVAX",
        "LINK",
        "BNB",
        "SOL",
        "AAVE",
        "UNI",
        "ENS",
    }
    DAO_ALIASES = {
        "aave": "aave.eth",
        "ens": "ens.eth",
        "uniswap": "uniswapgovernance.eth",
        "uniswapgovernance": "uniswapgovernance.eth",
        "compound": "compound-governance.eth",
    }
    TOKEN_KEYWORDS = {
        "token",
        "price",
        "chart",
        "kline",
        "volume",
        "market",
        "trend",
        "coin",
        "价格",
        "行情",
        "走势",
        "k线",
        "图表",
        "成交量",
        "涨跌",
        "涨幅",
        "跌幅",
        "币",
        "代币",
    }
    DAO_KEYWORDS = {
        "dao",
        "governance",
        "proposal",
        "proposals",
        "space",
        "snapshot",
        "治理",
        "提案",
        "投票",
        "社区",
    }
    SIMILAR_PROPOSAL_KEYWORDS = {
        "similar",
        "related",
        "recommend",
        "recommendation",
        "相似",
        "类似",
        "相关",
        "推荐",
    }
    PROPOSAL_DETAIL_KEYWORDS = {
        "summary",
        "summarize",
        "detail",
        "details",
        "keyword",
        "keywords",
        "explain",
        "总结",
        "概括",
        "详情",
        "关键词",
        "解释",
    }

    SYMBOL_PATTERN = re.compile(r"\b[A-Za-z]{2,10}\b")
    PROPOSAL_ID_PATTERN = re.compile(r"\b(?:0x[a-fA-F0-9]{8,}|[a-zA-Z0-9_-]{12,})\b")
    SPACE_ID_PATTERN = re.compile(r"\b[a-zA-Z0-9_-]+\.eth\b")

    def detect_intent(self, message: str, mode: AIChatMode = "auto") -> AIIntentResult:
        text = (message or "").strip()
        lower_text = text.lower()

        entities = self.extract_entities(text)
        scores = {
            "token": self._score_token(lower_text, entities),
            "dao": self._score_dao(lower_text, entities),
            "proposal": self._score_proposal(lower_text, entities),
        }

        if mode != "auto":
            selected_mode = mode
            confidence = max(scores.get(mode, 0.65), 0.65)
        else:
            selected_mode = max(scores, key=scores.get)
            confidence = scores[selected_mode]
            if confidence <= 0:
                selected_mode = "auto"
                confidence = 0.2

        required_tools = self._required_tools(selected_mode, lower_text, entities)
        return AIIntentResult(
            mode=selected_mode,
            confidence=round(float(confidence), 2),
            entities=entities,
            required_tools=required_tools,
        )

    def extract_entities(self, message: str) -> dict[str, object]:
        text = message or ""
        lower_text = text.lower()

        symbols = []
        for match in self.SYMBOL_PATTERN.findall(text):
            symbol = match.upper()
            if symbol in self.TOKEN_SYMBOLS:
                symbols.append(symbol)

        space_ids = list(dict.fromkeys(self.SPACE_ID_PATTERN.findall(lower_text)))
        dao_aliases = []
        for alias, space_id in self.DAO_ALIASES.items():
            if alias in lower_text:
                dao_aliases.append(alias)
                if space_id not in space_ids:
                    space_ids.append(space_id)

        proposal_ids = [
            value
            for value in self.PROPOSAL_ID_PATTERN.findall(text)
            if value.lower() not in set(space_ids) and value.upper() not in self.TOKEN_SYMBOLS
        ]

        return {
            "symbols": list(dict.fromkeys(symbols)),
            "space_ids": space_ids,
            "dao_aliases": list(dict.fromkeys(dao_aliases)),
            "proposal_ids": list(dict.fromkeys(proposal_ids)),
        }

    def _score_token(self, lower_text: str, entities: dict[str, object]) -> float:
        score = 0.0
        if entities.get("symbols"):
            score += 0.45
        score += 0.08 * self._keyword_hits(lower_text, self.TOKEN_KEYWORDS)
        return min(score, 0.95)

    def _score_dao(self, lower_text: str, entities: dict[str, object]) -> float:
        score = 0.0
        if entities.get("space_ids") or entities.get("dao_aliases"):
            score += 0.45
        score += 0.08 * self._keyword_hits(lower_text, self.DAO_KEYWORDS)
        return min(score, 0.95)

    def _score_proposal(self, lower_text: str, entities: dict[str, object]) -> float:
        score = 0.0
        if entities.get("proposal_ids"):
            score += 0.5
        score += 0.1 * self._keyword_hits(lower_text, self.SIMILAR_PROPOSAL_KEYWORDS)
        score += 0.06 * self._keyword_hits(lower_text, self.PROPOSAL_DETAIL_KEYWORDS)
        if "proposal" in lower_text or "提案" in lower_text:
            score += 0.2
        return min(score, 0.95)

    @staticmethod
    def _keyword_hits(lower_text: str, keywords: set[str]) -> int:
        return sum(1 for keyword in keywords if keyword.lower() in lower_text)

    def _required_tools(
        self,
        mode: AIChatMode,
        lower_text: str,
        entities: dict[str, object],
    ) -> list[str]:
        if mode == "token":
            tools = ["get_token_detail"]
            if self._keyword_hits(lower_text, {"chart", "kline", "trend", "走势", "k线", "图表"}):
                tools.append("get_token_chart")
            return tools

        if mode == "dao":
            if entities.get("space_ids") or entities.get("dao_aliases"):
                return ["list_proposals"]
            return ["get_dao_spaces"]

        if mode == "proposal":
            tools = []
            if entities.get("proposal_ids"):
                tools.append("get_proposal_detail")
            if self._keyword_hits(lower_text, self.SIMILAR_PROPOSAL_KEYWORDS):
                tools.append("search_similar_proposals")
            if not tools:
                tools.append("list_proposals")
            return tools

        return []
