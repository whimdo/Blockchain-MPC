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

    def is_low_quality_proposal(
        self,
        proposal: SnapshotProposal,
        min_title_len: int = 3,
        min_content_len: int = 40,
    ) -> bool:
        """
        Determine whether a normalized Snapshot proposal is low quality.

        Current rules:
        1) Missing title
        2) Both body and discussion are empty
        3) Title and total content are too short
        """
        if not proposal:
            return True

        title = self.clean_text(proposal.title or "")
        body = self.clean_text(proposal.body or "")
        discussion = self.clean_text(proposal.discussion or "")
        content = f"{body} {discussion}".strip()

        if not title:
            return True

        if not body and not discussion:
            return True

        if len(title) < min_title_len and len(content) < min_content_len:
            return True

        return False

    def is_low_quality_proposal_raw(
            self, 
            raw: dict[str, Any], 
            min_title_len: int = 3, 
            min_content_len: int = 40
    ) -> bool:
        '''
        Determine whether a raw Snapshot proposal payload is 
        low quality using the same rules as the normalized version. 
        This can be used to skip normalization and vectorization for 
        obviously low-quality proposals.
        '''
        title = self.clean_text(raw.get("title", ""))
        body = self.clean_text(raw.get("body", ""))
        discussion = self.clean_text(raw.get("discussion", "") or "")
        content = f"{body} {discussion}".strip()

        if not title:
            return True

        if not body and not discussion:
            return True

        if len(title) < min_title_len and len(content) < min_content_len:
            return True

        return False

    def is_low_quality_proposal_raw_by_title_and_content(
            self,
            title: str,
            body: str, 
            discussion: str, 
            min_title_len: int = 3, 
            min_content_len: int = 40
        ) -> bool:
        '''
        Determine whether a raw Snapshot proposal is low quality using title, 
        body, and discussion text directly. 
        This can be used in scenarios where we want to quickly assess proposal 
        quality without constructing the full raw dict.
        '''
        title_clean = self.clean_text(title)
        body_clean = self.clean_text(body)
        discussion_clean = self.clean_text(discussion)
        content = f"{body_clean} {discussion_clean}".strip()

        if not title_clean:
            return True

        if not body_clean and not discussion_clean:
            return True

        if len(title_clean) < min_title_len and len(content) < min_content_len:
            return True

        return False

    def normalize_proposal(self, raw: dict[str, Any]) -> SnapshotProposal:
        title = self.clean_text(raw.get("title", ""))
        body = self.clean_text(raw.get("body", ""))
        discussion = self.clean_text(raw.get("discussion", "") or "")

        cleaned_text = f"Title: {title}\nBody: {body}"
        if discussion:
            cleaned_text += f"\nDiscussion: {discussion}"

        if self.is_low_quality_proposal_raw_by_title_and_content(title, body, discussion):
            self.logger.info(
                "Identified low-quality proposal during normalization proposal_id=%s space_id=%s",
                raw.get("id", ""),
                raw.get("space", {}).get("id", ""),
            )
            keywords = []
        else:
            keywords = self.ai_service.extract_keywords_list(cleaned_text, top_k=5)

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

        # if self.is_low_quality_proposal(proposal):
        #     self.logger.info(
        #         "Skip low-quality proposal proposal_id=%s space_id=%s",
        #         proposal.proposal_id,
        #         proposal.space_id,
        #     )
        #     return None

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
