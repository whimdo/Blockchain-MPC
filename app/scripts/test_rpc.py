from app.services.chain_rpc_service import ChainRPCService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_rpc")


def main() -> None:
    """Run a quick test for RPC chain health checks."""
    service = ChainRPCService()

    for chain in ["ethereum", "bsc", "polygon"]:
        try:
            logger.info("Chain health test started chain=%s", chain)
            result = service.get_chain_health(chain)
            print(f"{chain}: {result}")
        except Exception:
            logger.exception("Chain health test failed chain=%s", chain)


if __name__ == "__main__":
    main()
