from app.services.chain_rpc_service import ChainRPCService
from app.services.market_service import MarketService
from app.utils.logging_config import get_logger


logger = get_logger("app.main")


def main() -> None:
    """程序示例入口。"""
    chain_service = ChainRPCService()
    market_service = MarketService()

    try:
        logger.info("开始执行主流程")

        print("=== Chain Health ===")
        chain_health = chain_service.get_chain_health("ethereum")
        print(chain_health)

        print("\n=== Latest Block ===")
        latest_block = chain_service.get_block_summary("ethereum")
        print(latest_block)

        print("\n=== Wallet Overview ===")
        overview = market_service.get_wallet_assets_with_prices(
            address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
            chains=["eth", "bsc", "polygon"],
        )
        print(overview)

        logger.info("主流程执行完成")
    except Exception:
        logger.exception("主流程执行失败")
        raise


if __name__ == "__main__":
    main()
