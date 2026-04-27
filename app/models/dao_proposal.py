from __future__ import annotations

from pydantic import BaseModel, Field
from app.models.snapshot_models import SnapshotProposal, SnapshotProposalVector, SnapshotDAO

class ErrorResponse(BaseModel):
    code: str
    message: str

class DAO(SnapshotDAO):
    pass

class DAOOverviewResponse(BaseModel):
    page_updated_at: str
    dao_count: int
    daos: list[DAO] = Field(default_factory=list)

class ProposalListItem(BaseModel):
    proposal_id: str
    space_id: str
    author: str | None = None
    title: str
    state: str
    keywords: list[str] = Field(default_factory=list)


class DetailProposal(SnapshotProposal):
    pass

class ProposalListInDAORequest(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=12, ge=1, le=100)
    state: str | None = Field(default=None, description="Filter by proposal state, e.g. 'active', 'closed'")

class ProposalListInDAOResponse(BaseModel):
    page_updated_at: str
    space_id: str
    dao_name: str
    page: int
    page_size: int
    total: int = 0
    proposals: list[ProposalListItem] = Field(default_factory=list)


class ProposalStatusUpdateRequest(BaseModel):
    proposal_id: str
    space_id: str


class ProposalStatusUpdateResponse(BaseModel):
    proposal_id: str
    space_id: str
    state: str | None = None
    end: int | None = None
    choices: list[str] = Field(default_factory=list)
    scores: list[float] = Field(default_factory=list)
    scores_total: float | None = None
    scores_updated: int | None = None

class SimilarProposals(BaseModel):
    proposal_id: str
    space_id: str
    top_k: int
    similar_proposals: list[ProposalListItem] = Field(default_factory=list)

class DetailAndSimilarProposalsResponse(BaseModel):
    proposal: DetailProposal
    similar_proposals: SimilarProposals

class DynamicSynchronousProposalRequest(BaseModel):
    space_id: str
    latest_k: int = Field(default=10, description="Number of latest proposals to consider for similarity search")

class DynamicSynchronousProposalResponse(BaseModel):#动态访问snapshot API获取最新的一系列proposal
    fetched_count: int
    new_count: int
    recent_updated_count: int = 0
    proposals: list[ProposalListItem] = Field(default_factory=list)
