from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Iterable

from app.clients.ai_client import AIClient
from app.models.token_detail_models import TokenAISummary, TokenChartSummary
from app.utils.logging_config import get_logger


class AIService:
    """Service for AI-powered text processing."""

    def __init__(self) -> None:
        self.logger = get_logger("app.services.ai_service")
        self.client = AIClient()

    @staticmethod
    def clean_text(text: str) -> str:
        """Remove common noise from raw text."""
        if not text:
            return ""

        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"http[s]?://\S+", " ", cleaned)
        cleaned = re.sub(r"\!\[.*?\]\(.*?\)", " ", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\((.*?)\)", r"\1", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _format_keywords(keywords: Iterable[str]) -> str:
        """Return strict format: [ word1,word2,word3 ]"""
        items = [k.strip() for k in keywords if k and k.strip()]
        return f"[ {','.join(items)} ]" if items else "[ ]"

    @staticmethod
    def _parse_keywords_from_ai(raw: str, top_k: int) -> list[str]:
        """Parse model output into a keyword list and trim to top_k."""
        text = raw.strip()

        if "[" in text and "]" in text:
            left = text.find("[")
            right = text.rfind("]")
            text = text[left + 1:right].strip()

        parts = re.split(r"[,，\n]+", text)
        keywords: list[str] = []
        for part in parts:
            token = part.strip().strip("[]")
            if not token:
                continue
            if token not in keywords:
                keywords.append(token)
            if len(keywords) >= top_k:
                break
        return keywords

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _safe_float(value: float | None) -> float:
        try:
            return float(value) if value is not None else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _fallback_keywords(text: str, top_k: int) -> list[str]:
        """
        Lightweight fallback extraction:
        - English words: length >= 3
        - Chinese chunks: length >= 2
        """
        english_words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", text.lower())
        chinese_words = re.findall(r"[\u4e00-\u9fff]{2,}", text)

        stopwords = {
            "the", "and", "for", "that", "this", "with", "from", "are",
            "was", "will", "have", "has", "not", "you", "but", "our",
            "can", "all", "your", "into", "about", "should", "more",
            "than", "been", "which", "their",
        }

        freq: dict[str, int] = {}
        for token in english_words + chinese_words:
            if token in stopwords:
                continue
            freq[token] = freq.get(token, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_k]]

    def extract_keywords_list(self, text: str, top_k: int = 5) -> list[str]:
        """Extract top_k keywords using AI first, then fallback."""
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []

        system_prompt = (
            "You are a keyword extraction assistant. "
            "Return exactly N keywords only, no explanation, in English."
        )
        user_prompt = (
            f"Extract {top_k} keywords from the following text.\n"
            "Output format must be exactly like this:\n"
            "[ word1,word2,word3 ]\n"
            "Use English delimiter ','.\n"
            f"Text:\n{cleaned_text}"
        )

        try:
            raw = self.client.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                max_tokens=256,
            )
            keywords = self._parse_keywords_from_ai(raw, top_k=top_k)
            if keywords:
                self.logger.info("AI keyword extraction success top_k=%s", top_k)
                return keywords
        except Exception:
            self.logger.exception("AI keyword extraction failed, using fallback")

        fallback = self._fallback_keywords(cleaned_text, top_k=top_k)
        self.logger.info("Fallback keyword extraction success top_k=%s", top_k)
        return fallback

    def extract_keywords_strict(self, text: str, top_k: int = 10) -> str:
        """Public method returning strict format string."""
        keywords = self.extract_keywords_list(text=text, top_k=top_k)
        return self._format_keywords(keywords)


    def generate_token_ai_summary(
        self,
        symbol: str,
        chart_summary: TokenChartSummary,
    ) -> TokenAISummary:
        """
        Generate structured TokenAISummary from symbol and chart summary.
        """
        token_symbol = (symbol or "").strip().upper()
        if not token_symbol:
            raise ValueError("symbol cannot be empty")

        cs = chart_summary or TokenChartSummary()
        change_percent = self._safe_float(cs.change_percent)
        start_price = self._safe_float(cs.start_price)
        end_price = self._safe_float(cs.end_price)
        high_price = self._safe_float(cs.high)
        low_price = self._safe_float(cs.low)
        total_quote_volume = self._safe_float(cs.total_quote_volume)
        total_trades = int(cs.total_trades or 0)

        system_prompt = (
            "You are a crypto market summarization assistant. "
            "Return strict JSON only with keys: title, summary, key_points, risk_notes."
        )
        user_prompt = (
            "1. 不要给出投资建议。2. 不要编造新闻或外部原因。3. 如果数据只包含行情数据，只能描述价格、成交量和趋势。4. 输出包括：一句标题、2-4 段解释、风险提示。5. 语气客观、简洁，适合展示在 Token 详情页。"
            f"symbol={token_symbol}\n"
            f"change_percent={change_percent}\n"
            f"start_price={start_price}\n"
            f"end_price={end_price}\n"
            f"high={high_price}\n"
            f"low={low_price}\n"
            f"total_quote_volume={total_quote_volume}\n"
            f"total_trades={total_trades}\n\n"
            "Write concise Chinese output.\n"
            "key_points should contain 3-5 items.\n"
            "risk_notes should contain 2 items.\n"
            "Output JSON only."
            "In chinese"
        )

        try:
            raw = self.client.chat_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=600,
            )
            parsed = json.loads(raw)
            return TokenAISummary(
                symbol=token_symbol,
                title=str(parsed.get("title") or f"为什么 {token_symbol} 最近上涨？"),
                summary=str(parsed.get("summary") or ""),
                key_points=[str(x) for x in (parsed.get("key_points") or [])],
                risk_notes=[str(x) for x in (parsed.get("risk_notes") or [])],
                generated_by="llm",
                generated_at=self._utc_now_iso(),
            )
        except Exception:
            self.logger.exception("LLM summary generation failed symbol=%s, fallback to template", token_symbol)

        direction = "上涨" if change_percent >= 0 else "下跌"
        return TokenAISummary(
            symbol=token_symbol,
            title=f"为什么 {token_symbol} 最近{direction}？",
            summary=(
                f"过去一段时间内，{token_symbol} 价格变动约 {change_percent:.2f}%，"
                f"区间价格在 {low_price:.2f} - {high_price:.2f}。"
                f"成交额约 {total_quote_volume:.2f}，成交笔数约 {total_trades}，"
                "市场活跃度存在波动，需注意短期回调风险。"
            ),
            key_points=[
                f"价格阶段变动约 {change_percent:.2f}%",
                f"区间起始价格约 {start_price:.2f}，结束价格约 {end_price:.2f}",
                f"区间高低点约 {high_price:.2f}/{low_price:.2f}",
                f"成交额约 {total_quote_volume:.2f}，成交笔数约 {total_trades}",
            ],
            risk_notes=[
                "该总结基于行情数据生成，不构成投资建议",
                "短期价格波动可能受外部新闻和宏观市场影响",
            ],
            generated_by="template",
            generated_at=self._utc_now_iso(),
        )