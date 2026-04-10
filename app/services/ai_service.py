from __future__ import annotations

import re
from typing import Iterable

from app.clients.ai_client import AIClient
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
        """
        Return strict format:
        [ word1、word2、word3 ]
        """
        items = [k.strip() for k in keywords if k and k.strip()]
        return f"[ {'、'.join(items)} ]" if items else "[ ]"

    @staticmethod
    def _parse_keywords_from_ai(raw: str, top_k: int) -> list[str]:
        """Parse model output into a keyword list and trim to top_k."""
        text = raw.strip()

        if "[" in text and "]" in text:
            left = text.find("[")
            right = text.rfind("]")
            text = text[left + 1:right].strip()

        parts = re.split(r"[、,，;\n]+", text)
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

    def extract_keywords_list(self, text: str, top_k: int = 10) -> list[str]:
        """Extract top_k keywords using AI first, then fallback."""
        if top_k <= 0:
            raise ValueError("top_k must be > 0")

        cleaned_text = self.clean_text(text)
        if not cleaned_text:
            return []

        system_prompt = (
            "You are a keyword extraction assistant. "
            "Return exactly N keywords only, no explanation."
        )
        user_prompt = (
            f"Extract {top_k} keywords from the following text.\n"
            "Output format must be exactly like this:\n"
            "[ word1、word2、word3 ]\n"
            "Use Chinese delimiter '、'.\n"
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
                print("ai keywords:", keywords)
                return keywords
        except Exception:
            self.logger.exception("AI keyword extraction failed, using fallback")

        fallback = self._fallback_keywords(cleaned_text, top_k=top_k)
        self.logger.info("Fallback keyword extraction success top_k=%s", top_k)
        return fallback

    def extract_keywords_strict(self, text: str, top_k: int = 10) -> str:
        """
        Public method:
        Input text, return strict format string: [ word1、word2、word3 ]
        """
        keywords = self.extract_keywords_list(text=text, top_k=top_k)
        return self._format_keywords(keywords)

