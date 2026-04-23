from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.models.snapshot_models import SnapshotProposal
from app.services.snapshot_service import SnapshotService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_snapshot_similarity_search")


def _print_results(title: str, items: list[SnapshotProposal]) -> None:
    print(f"\n[{title}] matched={len(items)}")
    for idx, proposal in enumerate(items, start=1):
        print(
            f"{idx}. proposal_id={proposal.proposal_id} | "
            f"space_id={proposal.space_id} | "
            f"title={proposal.title}"
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke test for SnapshotService similarity search methods:\n"
            "1) search_similar_proposals_by_keywords\n"
            "2) search_similar_proposals_by_text"
        )
    )
    parser.add_argument(
        "--keywords",
        nargs="+",
        default=["governance", "treasury", "funding"],
        help="Keyword list for keyword-vector search.",
    )
    parser.add_argument(
        "--text",
        default="A governance proposal about treasury budget allocation and grants.",
        help="Query text for text-vector search.",
    )
    parser.add_argument(
        "--space-id",
        default=None,
        help="Optional Snapshot space_id filter, e.g. aave.eth",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Top K results for each search.",
    )
    parser.add_argument(
        "--only",
        choices=["keywords", "text", "both"],
        default="both",
        help="Run only one method or both.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    service = SnapshotService()

    logger.info(
        "Snapshot similarity search test started space_id=%s top_k=%s only=%s",
        args.space_id,
        args.top_k,
        args.only,
    )

    try:
        if args.only in ("keywords", "both"):
            keyword_results = service.search_similar_proposals_by_keywords(
                keywords=args.keywords,
                space_id=args.space_id,
                top_k=args.top_k,
            )
            _print_results("KEYWORD SEARCH", keyword_results)

        if args.only in ("text", "both"):
            text_results = service.search_similar_proposals_by_text(
                text=args.text,
                space_id=args.space_id,
                top_k=args.top_k,
            )
            _print_results("TEXT SEARCH", text_results)

        logger.info("Snapshot similarity search test completed")
        print("\n[DONE] Snapshot similarity search test passed.")
        return 0
    except Exception:
        logger.exception("Snapshot similarity search test failed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
