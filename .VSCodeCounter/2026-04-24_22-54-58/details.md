# Details

Date : 2026-04-24 22:54:58

Directory e:\\-bishe\\Blockchain-MPC\\app

Total : 48 files,  4621 codes, 661 comments, 895 blanks, all 6177 lines

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)

## Files
| filename | language | code | comment | blank | total |
| :--- | :--- | ---: | ---: | ---: | ---: |
| [app/api/dao\_proposal.py](/app/api/dao_proposal.py) | Python | 91 | 0 | 13 | 104 |
| [app/api/dashboard\_tokens.py](/app/api/dashboard_tokens.py) | Python | 77 | 0 | 11 | 88 |
| [app/api/token\_detail.py](/app/api/token_detail.py) | Python | 86 | 0 | 18 | 104 |
| [app/clients/ai\_client.py](/app/clients/ai_client.py) | Python | 58 | 3 | 12 | 73 |
| [app/clients/ankr\_api\_client.py](/app/clients/ankr_api_client.py) | Python | 50 | 4 | 11 | 65 |
| [app/clients/binance\_client.py](/app/clients/binance_client.py) | Python | 128 | 18 | 25 | 171 |
| [app/clients/kafka\_client.py](/app/clients/kafka_client.py) | Python | 58 | 2 | 16 | 76 |
| [app/clients/milvus\_client.py](/app/clients/milvus_client.py) | Python | 25 | 2 | 12 | 39 |
| [app/clients/mongo\_client.py](/app/clients/mongo_client.py) | Python | 22 | 2 | 9 | 33 |
| [app/clients/multichain\_client.py](/app/clients/multichain_client.py) | Python | 130 | 9 | 20 | 159 |
| [app/clients/snapshot\_client.py](/app/clients/snapshot_client.py) | Python | 69 | 302 | 6 | 377 |
| [app/clients/token\_detail\_market\_client.py](/app/clients/token_detail_market_client.py) | Python | 10 | 5 | 8 | 23 |
| [app/main.py](/app/main.py) | Python | 8 | 0 | 4 | 12 |
| [app/models/chain\_models.py](/app/models/chain_models.py) | Python | 36 | 0 | 7 | 43 |
| [app/models/dao\_proposal.py](/app/models/dao_proposal.py) | Python | 40 | 0 | 12 | 52 |
| [app/models/dashboard\_tokens\_models.py](/app/models/dashboard_tokens_models.py) | Python | 37 | 0 | 17 | 54 |
| [app/models/snapshot\_models.py](/app/models/snapshot_models.py) | Python | 47 | 3 | 14 | 64 |
| [app/models/symbol\_mapper.py](/app/models/symbol_mapper.py) | Python | 86 | 18 | 18 | 122 |
| [app/models/token\_detail\_models.py](/app/models/token_detail_models.py) | Python | 95 | 1 | 28 | 124 |
| [app/models/token\_models.py](/app/models/token_models.py) | Python | 34 | 8 | 12 | 54 |
| [app/modules/proposals\_get\_and\_push.py](/app/modules/proposals_get_and_push.py) | Python | 123 | 6 | 26 | 155 |
| [app/modules/proposals\_vectorized\_and\_store.py](/app/modules/proposals_vectorized_and_store.py) | Python | 137 | 14 | 29 | 180 |
| [app/scripts/fill\_missing\_price.py](/app/scripts/fill_missing_price.py) | Python | 34 | 0 | 14 | 48 |
| [app/scripts/test\_assets.py](/app/scripts/test_assets.py) | Python | 18 | 2 | 8 | 28 |
| [app/scripts/test\_get\_one\_dao.py](/app/scripts/test_get_one_dao.py) | Python | 90 | 22 | 24 | 136 |
| [app/scripts/test\_keyword\_ai.py](/app/scripts/test_keyword_ai.py) | Python | 32 | 3 | 10 | 45 |
| [app/scripts/test\_mongo\_storage.py](/app/scripts/test_mongo_storage.py) | Python | 50 | 3 | 16 | 69 |
| [app/scripts/test\_prices.py](/app/scripts/test_prices.py) | Python | 15 | 1 | 8 | 24 |
| [app/scripts/test\_rpc.py](/app/scripts/test_rpc.py) | Python | 14 | 1 | 8 | 23 |
| [app/scripts/test\_snapshot\_similarity\_search.py](/app/scripts/test_snapshot_similarity_search.py) | Python | 88 | 0 | 19 | 107 |
| [app/scripts/test\_wallet\_overview.py](/app/scripts/test_wallet_overview.py) | Python | 18 | 1 | 8 | 27 |
| [app/services/ai\_service.py](/app/services/ai_service.py) | Python | 184 | 14 | 29 | 227 |
| [app/services/asset\_service.py](/app/services/asset_service.py) | Python | 28 | 3 | 4 | 35 |
| [app/services/chain\_rpc\_service.py](/app/services/chain_rpc_service.py) | Python | 42 | 6 | 8 | 56 |
| [app/services/dao\_proposal\_service.py](/app/services/dao_proposal_service.py) | Python | 247 | 0 | 43 | 290 |
| [app/services/dashboard\_tokens\_service.py](/app/services/dashboard_tokens_service.py) | Python | 267 | 1 | 37 | 305 |
| [app/services/market\_service.py](/app/services/market_service.py) | Python | 107 | 8 | 18 | 133 |
| [app/services/milvus\_service.py](/app/services/milvus_service.py) | Python | 183 | 26 | 29 | 238 |
| [app/services/price\_service.py](/app/services/price_service.py) | Python | 288 | 30 | 32 | 350 |
| [app/services/snapshot\_service.py](/app/services/snapshot_service.py) | Python | 352 | 24 | 62 | 438 |
| [app/services/symbol\_mapper\_service.py](/app/services/symbol_mapper_service.py) | Python | 38 | 45 | 14 | 97 |
| [app/services/token\_detail\_demo\_service.py](/app/services/token_detail_demo_service.py) | Python | 321 | 1 | 42 | 364 |
| [app/services/token\_detail\_service.py](/app/services/token_detail_service.py) | Python | 272 | 2 | 45 | 319 |
| [app/services/vector\_service.py](/app/services/vector_service.py) | Python | 140 | 16 | 30 | 186 |
| [app/storage/market\_storage.py](/app/storage/market_storage.py) | Python | 256 | 38 | 30 | 324 |
| [app/storage/snapshot\_storage.py](/app/storage/snapshot_storage.py) | Python | 59 | 15 | 14 | 88 |
| [app/utils/\_\_init\_\_.py](/app/utils/__init__.py) | Python | 0 | 1 | 2 | 3 |
| [app/utils/logging\_config.py](/app/utils/logging_config.py) | Python | 31 | 1 | 13 | 45 |

[Summary](results.md) / Details / [Diff Summary](diff.md) / [Diff Details](diff-details.md)