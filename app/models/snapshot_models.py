from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SnapshotProposal:
    proposal_id: str
    space_id: str
    space_name: str | None = None

    title: str = ""
    body: str = ""
    discussion: str | None = None
    author: str | None = None

    state: str | None = None
    start: int | None = None
    end: int | None = None
    snapshot: str | None = None

    choices: list[str] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    scores_total: float | None = None
    scores_updated: int | None = None
    created: int | None = None
    link: str | None = None

    source: str = "snapshot"

    cleaned_text: str | None = None
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SnapshotProposalVector:
    proposal_id: str
    space_id: str
    #text: str
    #keywords: list[str]
    #embedding_model: str
    vector: list[float]
    keyword_vector: list[float]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
    
@dataclass
class SnapshotDAO:
    name: str
    space_id: str
    logo: str | None = None
    description: str | None = None
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    latest_synchronization_time:str| None = None
    synchronized_proposals_count: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)