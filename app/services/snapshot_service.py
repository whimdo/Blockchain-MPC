from __future__ import annotations

import re
from typing import Any

from app.models.snapshot_models import SnapshotProposal
from app.utils.logging_config import get_logger
from app.clients.snapshot_client import SnapshotClient
from app.services.ai_service import AIService


class SnapshotService:
    def __init__(self) -> None:
        self.logger = get_logger("app.services.snapshot_service")
        self.ai_service = AIService()
        self.client = SnapshotClient()

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""

        # 去掉 HTML 标签
        text = re.sub(r"<[^>]+>", " ", text)
        # 去掉 URL
        text = re.sub(r"http[s]?://\S+", " ", text)
        # 去掉 markdown 图片/链接的部分噪声
        text = re.sub(r"\!\[.*?\]\(.*?\)", " ", text)
        text = re.sub(r"\[([^\]]+)\]\((.*?)\)", r"\1", text)
        # 合并空白
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def extract_keywords_num_count(text: str, top_k: int = 10) -> list[str]:# --- IGNORE ---
        """
        简单版本。
        你后面可以直接替换成你自己的关键词提取程序。
        """
        words = re.findall(r"[A-Za-z][A-Za-z0-9_\-]{2,}", text.lower())

        stopwords = {
            "the", "and", "for", "that", "this", "with", "from", "are",
            "was", "will", "have", "has", "not", "you", "but", "our",
            "can", "all", "your", "into", "about", "should", "more",
            "than", "been", "which", "their", "proposal", "snapshot"
        }

        freq: dict[str, int] = {}
        for word in words:
            if word in stopwords:
                continue
            freq[word] = freq.get(word, 0) + 1

        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_k]]

    def normalize_proposal(self, raw: dict[str, Any]) -> SnapshotProposal:
        title = self.clean_text(raw.get("title", ""))
        body = self.clean_text(raw.get("body", ""))
        discussion = self.clean_text(raw.get("discussion", "") or "")

        cleaned_text = f"Title: {title}\nBody: {body}"
        if discussion:
            cleaned_text += f"\nDiscussion: {discussion}"

        keywords = self.ai_service.extract_keywords_list(cleaned_text, top_k=10)

        space = raw.get("space", {}) or {}

        return SnapshotProposal(
            proposal_id=raw.get("id", ""),
            space_id=space.get("id", ""),
            space_name=space.get("name"),
            title=title,
            body=body,
            discussion=discussion or None,
            author=raw.get("author"),
            state=raw.get("state"),
            start=raw.get("start"),
            end=raw.get("end"),
            snapshot=raw.get("snapshot"),
            choices=raw.get("choices", []) or [],
            scores=raw.get("scores", []) or [],
            scores_total=raw.get("scores_total"),
            scores_updated=raw.get("scores_updated"),
            created=raw.get("created"),
            link=raw.get("link"),
            cleaned_text=cleaned_text,
            keywords=keywords,
        )

    def fetch_and_normalize_proposals(
        self,
        space_id: str,
        first: int = 20,
        skip: int = 0,
    ) -> list[SnapshotProposal]:
        raw_proposals = self.client.get_space_proposals(
            space_id=space_id,
            first=first,
            skip=skip,
        )

        proposals = [self.normalize_proposal(item) for item in raw_proposals]

        self.logger.info(
            "Normalized Snapshot proposals space=%s count=%s",
            space_id,
            len(proposals),
        )
        return proposals