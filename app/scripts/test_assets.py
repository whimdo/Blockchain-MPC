from app.services.asset_service import AssetService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_assets")


def main() -> None:
    """Run a quick test for multi-chain asset query."""
    service = AssetService()
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    chains = ["eth", "bsc", "polygon"]

    try:
        logger.info("Asset query test started")
        result = service.get_multichain_assets(address, chains)
        print(result)
        logger.info("Asset query test completed")
    except Exception:
        logger.exception("Asset query test failed")
        raise


if __name__ == "__main__":
    main()
