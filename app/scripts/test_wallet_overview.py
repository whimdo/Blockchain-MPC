from app.services.market_service import MarketService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_wallet_overview")


def main() -> None:
    """Run a quick test for wallet overview aggregation."""
    service = MarketService()
    address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    chains = ["eth", "bsc", "polygon"]

    try:
        logger.info("Wallet overview test started")
        result = service.get_wallet_assets_with_prices(address, chains)
        print(result)
        logger.info("Wallet overview test completed")
    except Exception:
        logger.exception("Wallet overview test failed")
        raise


if __name__ == "__main__":
    main()
