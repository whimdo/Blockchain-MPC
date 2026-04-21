from __future__ import annotations

import re
from typing import Any

from app.models.snapshot_models import SnapshotProposal, SnapshotProposalVector
from app.utils.logging_config import get_logger
from app.clients.snapshot_client import SnapshotClient
from app.services.ai_service import AIService
from app.storage.snapshot_storage import SnapshotStorage
from app.services.vector_service import VectorService


class SnapshotService:
    def __init__(self) -> None:
        self.logger = get_logger("app.services.snapshot_service")
        self.storage = SnapshotStorage()
        self.ai_service = AIService()
        self.client = SnapshotClient()
        self.vector_service = VectorService()

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
    
    def get_proposal_vector(self, proposal: SnapshotProposal) -> SnapshotProposalVector | None:
        """Generate vector payload for a single normalized proposal."""
        if not proposal or not proposal.proposal_id or not proposal.space_id:
            self.logger.warning("Invalid proposal input for vectorization.")
            return None

        try:
            cleaned_text = (proposal.cleaned_text or "").strip()
            if not cleaned_text:
                title = self.clean_text(proposal.title or "")
                body = self.clean_text(proposal.body or "")
                discussion = self.clean_text(proposal.discussion or "")

                cleaned_text = f"Title: {title}\nBody: {body}"
                if discussion:
                    cleaned_text += f"\nDiscussion: {discussion}"

            keywords = [k for k in (proposal.keywords or []) if k and k.strip()]
            if not keywords:
                keywords = self.ai_service.extract_keywords_list(cleaned_text, top_k=10)

            text_vector = self.vector_service.embed_long_text(cleaned_text)
            keyword_vector = self.vector_service.embed_keywords(keywords)

            if not text_vector or not keyword_vector:
                self.logger.warning(
                    "Vector generation returned empty vector proposal_id=%s",
                    proposal.proposal_id,
                )
                return None

            return SnapshotProposalVector(
                proposal_id=proposal.proposal_id,
                space_id=proposal.space_id,
                vector=text_vector,
                keyword_vector=keyword_vector,
            )
        except Exception:
            self.logger.exception(
                "Failed to generate proposal vector proposal_id=%s",
                proposal.proposal_id,
            )
            return None
