from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse

from app.models.dao_proposal import (
    DAOOverviewResponse,
    DetailAndSimilarProposalsResponse,
    DynamicSynchronousProposalRequest,
    DynamicSynchronousProposalResponse,
    ErrorResponse,
    ProposalListInDAORequest,
    ProposalListInDAOResponse,
    ProposalStatusUpdateRequest,
    ProposalStatusUpdateResponse,
)
from app.services.dao_proposal_service import DaoProposalService, DaoProposalServiceError
from app.utils.logging_config import get_logger


logger = get_logger("app.api.dao_proposal")
router = APIRouter(prefix="/api/dao", tags=["dao-proposal"])
_service = DaoProposalService()


@router.get(
    "/overview",
    response_model=DAOOverviewResponse,
    responses={500: {"model": ErrorResponse}},
    summary="DAO Overview",
)
def get_dao_overview() -> DAOOverviewResponse | JSONResponse:
    try:
        return _service.get_dao_overview()
    except DaoProposalServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to build dao overview")
        return JSONResponse(
            status_code=500,
            content={"code": "DAO_OVERVIEW_ERROR", "message": "Failed to load dao overview."},
        )


@router.get(
    "/{space_id}/proposals",
    response_model=ProposalListInDAOResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Proposal List In DAO",
)
def get_proposals_in_dao(
    space_id: str,
    req: ProposalListInDAORequest = Depends(),
) -> ProposalListInDAOResponse | JSONResponse:
    try:
        return _service.get_proposals_in_dao(
            space_id=space_id,
            page=req.page,
            page_size=req.page_size,
            state=req.state,
        )
    except DaoProposalServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to load proposals in dao space_id=%s", space_id)
        return JSONResponse(
            status_code=500,
            content={"code": "DAO_PROPOSALS_ERROR", "message": "Failed to load dao proposals."},
        )


@router.post(
    "/proposal/status-update",
    response_model=ProposalStatusUpdateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Update Proposal Status",
)
def update_proposal_status(req: ProposalStatusUpdateRequest) -> ProposalStatusUpdateResponse | JSONResponse:
    try:
        return _service.update_proposal_status(proposal_id=req.proposal_id, space_id=req.space_id)
    except DaoProposalServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception(
            "Failed to update proposal status proposal_id=%s space_id=%s",
            req.proposal_id,
            req.space_id,
        )
        return JSONResponse(
            status_code=500,
            content={"code": "PROPOSAL_STATUS_UPDATE_ERROR", "message": "Failed to update proposal status."},
        )


@router.get(
    "/proposal/{proposal_id}",
    response_model=DetailAndSimilarProposalsResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Proposal Detail And Similar Proposals",
)
def get_proposal_detail_and_similar(
    proposal_id: str,
    top_k: int = Query(default=2, ge=1, le=20),
) -> DetailAndSimilarProposalsResponse | JSONResponse:
    try:
        return _service.get_proposal_detail_and_similar(proposal_id=proposal_id, top_k=top_k)
    except DaoProposalServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to load proposal detail proposal_id=%s", proposal_id)
        return JSONResponse(
            status_code=500,
            content={"code": "PROPOSAL_DETAIL_ERROR", "message": "Failed to load proposal detail."},
        )


@router.post(
    "/proposals/dynamic-sync",
    response_model=DynamicSynchronousProposalResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Dynamic Sync Latest Proposals",
)
def dynamic_sync_proposals(req: DynamicSynchronousProposalRequest) -> DynamicSynchronousProposalResponse | JSONResponse:
    try:
        return _service.dynamic_sync_proposals(space_id=req.space_id, latest_k=req.latest_k)
    except DaoProposalServiceError as exc:
        return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
    except Exception:
        logger.exception("Failed to dynamic sync proposals space_id=%s latest_k=%s", req.space_id, req.latest_k)
        return JSONResponse(
            status_code=500,
            content={"code": "DYNAMIC_SYNC_ERROR", "message": "Failed to sync latest proposals."},
        )
