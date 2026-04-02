from app.services.price_service import PriceService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.test_prices")


def main() -> None:
    """Run a quick test for Binance price query."""
    service = PriceService()

    try:
        logger.info("Price query test started")
        print(service.get_symbol_price("ETHUSDT"))
        print(service.get_symbols_price(["ETHUSDT", "BTCUSDT", "BNBUSDT"]))
        logger.info("Price query test completed")
    except Exception:
        logger.exception("Price query test failed")
        raise


if __name__ == "__main__":
    main()
