from __future__ import annotations

from app.services.price_service import PriceService
from app.utils.logging_config import get_logger


logger = get_logger("app.scripts.fill_missing_token_prices")


MISSING_TOKENS = [
    "AVAX",
    "XRP",
    "DOGE",
]


def main() -> None:
    service = PriceService()

    success_list: list[str] = []
    failed_list: list[str] = []

    logger.info("Start filling missing token prices count=%s", len(MISSING_TOKENS))

    for symbol in MISSING_TOKENS:
        try:
            result = service.update_get_token_price(symbol)
            logger.info("Filled token price success symbol=%s result=%s", symbol, result)
            success_list.append(symbol)
        except Exception:
            logger.exception("Filled token price failed symbol=%s", symbol)
            failed_list.append(symbol)

    logger.info(
        "Fill missing token prices done success_count=%s failed_count=%s success=%s failed=%s",
        len(success_list),
        len(failed_list),
        success_list,
        failed_list,
    )

    print("=== Fill Missing Token Prices Done ===")
    print(f"Success ({len(success_list)}): {success_list}")
    print(f"Failed  ({len(failed_list)}): {failed_list}")


if __name__ == "__main__":
    main()