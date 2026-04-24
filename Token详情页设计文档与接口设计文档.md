# Token 详情页设计文档与接口设计文档

## 一、文档目标

本文档用于规划 Dashboard 中“Token 详情页”的产品结构、数据来源、页面模块和后端 API 接口。  
该详情页目标不是简单展示首页卡片信息，而是构建一个轻量级的 **Token Browser / Token Explorer** 页面。

页面需要支持：

- 展示 Token 基础信息
- 展示当前价格、24h 状态和数据更新时间
- 展示价格趋势图与成交量图
- 展示链上状态信息
- 提供 AI 总结与介绍
- 为后续扩展 Token holders、转账记录、治理关联信息预留结构

---

## 二、页面定位

Token 详情页定位为：

> 面向某个 Token 的综合浏览页面，聚合市场数据、链上状态、基础资料与 AI 总结能力。

该页面不是交易页面，也不是完整区块浏览器，而是平台中连接：

- Dashboard 总览
- 链上数据能力
- 市场行情能力
- AI 智能分析能力

的中间页面。

---

## 三、页面整体结构

Token 详情页建议由以下模块组成：

1. 顶部 Token 概览区
2. 价格趋势图表区
3. 基础信息与链上状态区
4. 市场活跃数据区
5. AI 总结与介绍区

页面结构建议如下：

```text
Token Detail Page
├── 顶部 Token 概览区
├── 价格趋势图表区
├── 基础信息与链上状态区
├── 市场活跃数据区
└── AI 总结与介绍区
```

---

# 四、页面模块设计

---

## 4.1 顶部 Token 概览区

### 4.1.1 模块目标

顶部概览区用于让用户快速确认当前正在查看的 Token，并展示最核心的实时状态。

该区域应作为页面视觉重点，类似 TokenView、CoinMarketCap、CoinGecko 或区块链浏览器中的顶部资产概览。

---

### 4.1.2 展示内容

建议展示：

- Token Logo
- Token 名称
- Symbol
- 主链
- 分类标签
- 当前价格
- 24h 涨跌幅
- 24h 最高价
- 24h 最低价
- 24h 成交量
- 更新时间
- 数据状态
- 刷新按钮

---

### 4.1.3 字段说明

| 字段 | 说明 | 数据来源 |
|---|---|---|
| symbol | Token 简称 | YAML 配置 |
| name | Token 全称 | YAML 配置 |
| display_name | 前端展示名 | YAML 配置 |
| logo | Token 图标 | YAML 配置 |
| primary_chain | 主链 | YAML 配置 |
| category | 分类 | YAML 配置 |
| tags | 标签 | YAML 配置 |
| price | 当前价格 | Binance / CoinGecko / Mongo 缓存 |
| price_display | 前端展示价格 | 后端格式化 |
| price_change_24h | 24h 涨跌幅 | Binance 24hr ticker / CoinGecko |
| high_24h | 24h 最高价 | Binance 24hr ticker / CoinGecko |
| low_24h | 24h 最低价 | Binance 24hr ticker / CoinGecko |
| volume_24h | 24h 成交量 | Binance 24hr ticker / CoinGecko |
| updated_at | 更新时间 | 后端聚合时间 |
| status | 数据状态 | 后端聚合判断 |

---

### 4.1.4 数据来源规划

#### 静态信息

来自：

```text
configs/dashboard_tokens_config.yaml
```

包括：

- symbol
- name
- display_name
- primary_chain
- category
- logo
- description
- tags
- price_symbol

#### 动态市场信息

优先来源：

- Binance 24hr ticker
- Binance current price
- CoinGecko coins/markets

#### 本地缓存

来自：

- MongoDB token price collection
- price_history
- token current price

---

## 4.2 价格趋势图表区

### 4.2.1 模块目标

价格趋势图表区用于展示 Token 在不同时间范围内的价格变化趋势，使详情页更像正式的 Token 浏览器页面。

---

### 4.2.2 展示内容

建议展示：

- 价格折线图或面积图
- 成交量柱状图
- 时间范围切换按钮

时间范围建议：

- 1D
- 7D
- 1M
- 3M
- 1Y

第一版建议优先支持：

- 1D
- 7D
- 1M

---

### 4.2.3 图表数据字段

每个价格点建议包含：

| 字段 | 说明 |
|---|---|
| timestamp | 时间点 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 成交量 |
| trades_count | 成交笔数，可选 |

---

### 4.2.4 推荐数据来源

#### 第一优先：Binance Kline / UIKlines

适合获取：

- OHLC
- 成交量
- 成交笔数
- 不同时间粒度价格图

推荐使用：

- `/api/v3/klines`
- `/api/v3/uiKlines`

推荐映射：

| 页面范围 | interval |
|---|---|
| 1D | 15m 或 1h |
| 7D | 1h |
| 1M | 4h 或 1d |
| 3M | 1d |
| 1Y | 1d 或 1w |

---

#### 第二优先：CoinGecko market_chart

适合获取：

- 聚合价格
- 市值趋势
- 24h volume 趋势
- 非 Binance 交易对覆盖资产

需要维护：

- symbol 到 CoinGecko coin_id 的映射

例如：

| Symbol | CoinGecko ID |
|---|---|
| BTC | bitcoin |
| ETH | ethereum |
| DOGE | dogecoin |
| XRP | ripple |
| AVAX | avalanche-2 |

---

#### 第三来源：MongoDB price_history

适合展示：

- 系统内部采集历史
- Binance 与 Ankr 的价格对比
- 本平台价格同步记录

不建议作为主价格图唯一来源，因为采样不够稳定。

---

## 4.3 基础信息与链上状态区

### 4.3.1 模块目标

基础信息与链上状态区用于展示 Token 的基本资料和平台当前能够获取到的链上状态。

建议采用左右两张卡片布局：

```text
左侧：基础信息卡
右侧：链上状态卡
```

---

## 4.3.2 基础信息卡

### 展示内容

- Token 名称
- Symbol
- 主链
- 分类
- 标签
- 简短介绍
- 价格查询交易对
- 是否首页展示

### 数据来源

来自：

```text
dashboard_tokens_config.yaml
```

该部分数据为静态配置，不需要实时查询。

---

## 4.3.3 链上状态卡

### 展示内容

- 主链名称
- 是否已接入 RPC
- RPC 状态
- 最新区块号
- 最新区块时间
- 当前 gas price
- 链上查询能力状态

---

### 数据来源

优先来源：

- 现有 RPC client
- Ankr RPC
- Ankr Advanced API

对于已接入链：

- Ethereum
- BSC
- Polygon

可以展示：

- latest_block
- gas_price
- rpc_status
- last_checked_at

对于未接入链：

- BTC
- XRP
- DOGE
- SOL
- ADA
- TRX

第一版可以显示：

- chain_supported: false
- rpc_status: unsupported
- onchain_data_status: not_integrated

这样更加真实，不需要伪造数据。

---

## 4.4 市场活跃数据区

### 4.4.1 模块目标

市场活跃数据区用于展示 Token 在市场层面的近期活跃程度。

该区域第一版建议展示交易所市场数据，而不是链上交易数。

---

### 4.4.2 第一版展示内容

建议展示：

- 24h 成交量
- 近几日成交量柱状图
- 成交笔数变化
- 最高价 / 最低价区间
- 最近价格变化幅度

---

### 4.4.3 数据来源

第一版推荐：

- Binance Kline volume
- Binance Kline number_of_trades
- Binance 24hr ticker

后续可扩展：

- CoinGecko volume
- Ankr Token API
- Etherscan / BscScan / PolygonScan
- 自建链上统计任务

---

## 4.5 AI 总结与介绍区

### 4.5.1 模块目标

AI 总结与介绍区用于用自然语言解释当前 Token 的基本情况、价格状态和链上状态。

第一版可以采用模板生成，后续再接入真正的 AI 服务。

---

### 4.5.2 展示内容

建议展示：

- Token 是什么
- 属于什么类型资产
- 当前价格状态
- 当前链上状态
- 是否支持平台进一步查询
- 数据来源说明

---

### 4.5.3 第一版实现方式

第一版可采用模板生成：

```text
{display_name} 是一个 {category} 类型的加密资产，主链为 {primary_chain}。
当前价格为 {price_display}，24 小时涨跌幅为 {price_change_24h}。
当前数据状态为 {status}，最近更新时间为 {updated_at}。
```

---

### 4.5.4 第二版扩展

后续可接入：

- MCP AI 问答服务
- Token 相关新闻总结
- DAO proposal 关联分析
- 价格变化解释
- 风险提示生成

---

# 五、数据来源总体规划

## 5.1 静态配置数据

来源：

```text
configs/dashboard_tokens_config.yaml
```

用于：

- Token 名称
- Symbol
- Logo
- 主链
- 分类
- 标签
- 描述
- price_symbol
- CoinGecko ID（建议后续补充）
- 是否支持链上状态查询

---

## 5.2 当前价格数据

来源优先级：

1. Binance current price / 24hr ticker
2. CoinGecko coins/markets
3. MongoDB 当前价格缓存

---

## 5.3 历史价格与图表数据

来源优先级：

1. Binance Kline / UIKlines
2. CoinGecko market_chart
3. MongoDB price_history

---

## 5.4 链上状态数据

来源优先级：

1. 项目现有 RPC client
2. Ankr RPC
3. Ankr Advanced API
4. 区块链浏览器 API

---

## 5.5 Token holders / 转账数据

后续扩展来源：

- Ankr Token API
- Etherscan API
- BscScan API
- PolygonScan API

第一版不建议优先实现。

---

# 六、Token 详情页 API 设计

当前建议先设计三个接口：

1. Token 详情主接口
2. Token 图表接口
3. Token 刷新接口

---

# 七、接口一：Token 详情主接口

## 7.1 接口信息

### 接口名称

Token 详情主接口

### 请求方式

`GET`

### 请求路径

```text
/api/dashboard/tokens/detail
```

---

## 7.2 接口用途

用于进入某个 Token 详情页时获取页面基础展示数据。

该接口返回：

- 顶部概览信息
- 基础信息
- 当前价格状态
- 链上状态
- AI 总结文本

不建议该接口直接返回大量图表点位，图表数据应由单独图表接口提供。

---

## 7.3 请求参数

### symbol

类型：`string`

必填：是

示例：

```text
BTC
ETH
DOGE
```

示例请求：

```text
GET /api/dashboard/tokens/detail?symbol=BTC
```

---

## 7.4 返回结构

建议按页面模块返回：

```json
{
  "symbol": "BTC",
  "overview": {},
  "basic_info": {},
  "market_status": {},
  "chain_status": {},
  "ai_summary": {}
}
```

---

## 7.5 返回字段说明

### overview

用于顶部概览区。

| 字段 | 说明 |
|---|---|
| symbol | Token 简称 |
| name | Token 全称 |
| display_name | 展示名 |
| logo | 图标 |
| primary_chain | 主链 |
| category | 分类 |
| tags | 标签 |
| price_display | 当前价格展示 |
| updated_at | 更新时间 |
| status | 数据状态 |

---

### basic_info

用于基础信息卡。

| 字段 | 说明 |
|---|---|
| symbol | Token 简称 |
| name | Token 全称 |
| display_name | 展示名 |
| primary_chain | 主链 |
| category | 分类 |
| price_symbol | Binance 查询交易对 |
| description | 简短介绍 |
| tags | 标签 |

---

### market_status

用于价格与市场状态。

| 字段 | 说明 |
|---|---|
| price | 当前价格 |
| price_display | 展示价格 |
| price_change_24h | 24h 涨跌幅 |
| high_24h | 24h 最高价 |
| low_24h | 24h 最低价 |
| volume_24h | 24h 成交量 |
| source | 数据来源 |
| updated_at | 更新时间 |

---

### chain_status

用于链上状态卡。

| 字段 | 说明 |
|---|---|
| primary_chain | 主链 |
| chain_supported | 是否接入该链 |
| rpc_status | RPC 状态 |
| latest_block | 最新区块号 |
| gas_price | 当前 gas price |
| last_checked_at | 最近检查时间 |
| onchain_data_status | 链上数据状态 |

---

### ai_summary

用于 AI 总结区。

| 字段 | 说明 |
|---|---|
| summary | 总结文本 |
| generated_by | template / ai |
| generated_at | 生成时间 |

---

## 7.6 返回示例

```json
{
  "symbol": "ETH",
  "overview": {
    "symbol": "ETH",
    "name": "Ethereum",
    "display_name": "Ethereum",
    "logo": "/assets/tokens/eth.png",
    "primary_chain": "ethereum",
    "category": "native",
    "tags": ["Layer1", "Native", "Smart Contract"],
    "price_display": "2052.69 USDT",
    "updated_at": "2026-04-23T22:30:00Z",
    "status": "online"
  },
  "basic_info": {
    "symbol": "ETH",
    "name": "Ethereum",
    "display_name": "Ethereum",
    "primary_chain": "ethereum",
    "category": "native",
    "price_symbol": "ETHUSDT",
    "description": "The native asset of Ethereum and a core asset for smart contract ecosystems.",
    "tags": ["Layer1", "Native", "Smart Contract"]
  },
  "market_status": {
    "price": 2052.69,
    "price_display": "2052.69 USDT",
    "price_change_24h": 2.31,
    "high_24h": 2090.12,
    "low_24h": 1988.35,
    "volume_24h": 1234567890.12,
    "source": "binance",
    "updated_at": "2026-04-23T22:30:00Z"
  },
  "chain_status": {
    "primary_chain": "ethereum",
    "chain_supported": true,
    "rpc_status": "online",
    "latest_block": 19752345,
    "gas_price": "12.5 gwei",
    "last_checked_at": "2026-04-23T22:30:00Z",
    "onchain_data_status": "available"
  },
  "ai_summary": {
    "summary": "Ethereum 是一个 native 类型的加密资产，主链为 ethereum，当前价格为 2052.69 USDT，当前链上状态正常。",
    "generated_by": "template",
    "generated_at": "2026-04-23T22:30:00Z"
  }
}
```

---

## 7.7 错误处理

### 参数缺失

HTTP 400

```json
{
  "code": "SYMBOL_REQUIRED",
  "message": "Query parameter 'symbol' is required."
}
```

### Token 不存在

HTTP 404

```json
{
  "code": "TOKEN_NOT_FOUND",
  "message": "Token configuration not found."
}
```

### 系统异常

HTTP 500

```json
{
  "code": "TOKEN_DETAIL_ERROR",
  "message": "Failed to load token detail."
}
```

---

# 八、接口二：Token 图表接口

## 8.1 接口信息

### 接口名称

Token 图表数据接口

### 请求方式

`GET`

### 请求路径

```text
/api/dashboard/tokens/chart
```

---

## 8.2 接口用途

用于获取 Token 详情页中的价格趋势图、成交量图和成交笔数图数据。

---

## 8.3 请求参数

### symbol

类型：`string`

必填：是

示例：

```text
BTC
ETH
DOGE
```

### range

类型：`string`

必填：否

默认值：

```text
7d
```

可选值：

- 1d
- 7d
- 1m
- 3m
- 1y

### interval

类型：`string`

必填：否

默认由后端根据 range 决定。

可选值：

- 15m
- 1h
- 4h
- 1d
- 1w

---

## 8.4 推荐 range 与 interval 映射

| range | 默认 interval |
|---|---|
| 1d | 15m |
| 7d | 1h |
| 1m | 4h |
| 3m | 1d |
| 1y | 1d |

---

## 8.5 返回结构

```json
{
  "symbol": "BTC",
  "range": "7d",
  "interval": "1h",
  "source": "binance",
  "price_points": [],
  "volume_points": []
}
```

---

## 8.6 返回字段说明

### price_points

每个点包含：

| 字段 | 说明 |
|---|---|
| timestamp | 时间 |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |

### volume_points

每个点包含：

| 字段 | 说明 |
|---|---|
| timestamp | 时间 |
| volume | 成交量 |
| quote_volume | 计价成交量 |
| trades_count | 成交笔数 |

---

## 8.7 返回示例

```json
{
  "symbol": "BTC",
  "range": "7d",
  "interval": "1h",
  "source": "binance",
  "price_points": [
    {
      "timestamp": "2026-04-23T00:00:00Z",
      "open": 76000.1,
      "high": 76500.2,
      "low": 75500.8,
      "close": 76220.5
    }
  ],
  "volume_points": [
    {
      "timestamp": "2026-04-23T00:00:00Z",
      "volume": 1234.56,
      "quote_volume": 94000000.12,
      "trades_count": 25678
    }
  ]
}
```

---

## 8.8 数据来源策略

### 第一优先

Binance Kline / UIKlines

### 第二优先

CoinGecko market_chart

### 第三优先

MongoDB price_history

当 Binance 不支持某个交易对时，可以回退到 CoinGecko。

---

## 8.9 错误处理

### Token 不存在

HTTP 404

```json
{
  "code": "TOKEN_NOT_FOUND",
  "message": "Token configuration not found."
}
```

### 图表数据不可用

HTTP 200

```json
{
  "symbol": "DOGE",
  "range": "7d",
  "interval": "1h",
  "source": "none",
  "price_points": [],
  "volume_points": [],
  "message": "Chart data is currently unavailable."
}
```

---

# 九、接口三：Token 刷新接口

## 9.1 接口信息

### 接口名称

Token 详情刷新接口

### 请求方式

`POST`

### 请求路径

```text
/api/dashboard/tokens/refresh
```

---

## 9.2 接口用途

用于用户在详情页点击“刷新”按钮时，重新获取当前价格和链上状态。

该接口可复用首页卡片刷新接口，但建议返回更完整的动态状态。

---

## 9.3 请求体

```json
{
  "symbol": "ETH"
}
```

---

## 9.4 返回结构

```json
{
  "symbol": "ETH",
  "market_status": {},
  "chain_status": {},
  "updated_at": "2026-04-23T22:40:00Z"
}
```

---

## 9.5 返回示例

```json
{
  "symbol": "ETH",
  "market_status": {
    "price": 2058.12,
    "price_display": "2058.12 USDT",
    "price_change_24h": 2.45,
    "high_24h": 2090.12,
    "low_24h": 1988.35,
    "volume_24h": 1234567890.12,
    "source": "binance",
    "updated_at": "2026-04-23T22:40:00Z"
  },
  "chain_status": {
    "primary_chain": "ethereum",
    "chain_supported": true,
    "rpc_status": "online",
    "latest_block": 19752355,
    "gas_price": "13.1 gwei",
    "last_checked_at": "2026-04-23T22:40:00Z",
    "onchain_data_status": "available"
  },
  "updated_at": "2026-04-23T22:40:00Z"
}
```

---

# 十、后端服务设计建议

建议新增或整理以下服务：

```text
app/services/dashboard_token_detail_service.py
```

负责：

- 读取 YAML 配置
- 调用 price_service
- 调用 Binance market data client
- 调用 RPC service
- 聚合返回详情页结构

---

## 10.1 推荐后端模块

| 模块 | 作用 |
|---|---|
| dashboard_config_service | 读取 dashboard_tokens_config.yaml |
| price_service | 当前价格与缓存 |
| market_chart_service | 获取 Kline / market_chart |
| chain_status_service | 获取 RPC 状态、最新区块 |
| token_detail_service | 聚合详情页数据 |
| ai_summary_service | 生成 AI 总结 |

---

## 10.2 推荐数据流

```text
前端请求 Token Detail
        ↓
TokenDetailService
        ↓
读取 YAML 静态配置
        ↓
获取当前价格与市场状态
        ↓
获取链上状态
        ↓
生成 AI Summary
        ↓
返回详情页结构
```

---

# 十一、12 个首页 Token 的数据来源建议

| Symbol | 当前价格 | 历史价格/成交量 | 链上状态 |
|---|---|---|---|
| BTC | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| ETH | Binance / CoinGecko | Binance Kline / CoinGecko | Ethereum RPC / Ankr |
| USDT | Binance / CoinGecko | Binance Kline / CoinGecko | Ethereum/BSC/Polygon Token API |
| USDC | Binance / CoinGecko | Binance Kline / CoinGecko | Ethereum Token API |
| BNB | Binance / CoinGecko | Binance Kline / CoinGecko | BSC RPC / Ankr |
| SOL | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| ADA | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| AVAX | Binance / CoinGecko / Ankr | Binance Kline / CoinGecko | Avalanche RPC / Ankr，可扩展 |
| XRP | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| TRX | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| DOGE | Binance / CoinGecko | Binance Kline / CoinGecko | 第一版可标记未接入 |
| LINK | Binance / CoinGecko | Binance Kline / CoinGecko | Ethereum Token API / Ankr |

---

# 十二、第一版实现优先级

## 第一优先级

1. Token 详情主接口
2. Binance Kline 图表接口
3. 当前价格与 24h 状态
4. AI 模板总结

---

## 第二优先级

1. RPC 状态精细化
2. CoinGecko 兜底
3. MongoDB price_history 对比展示

---

## 第三优先级

1. Token holders
2. Token transfers
3. 活跃地址
4. 链上交易数量图
5. 真实 AI 总结

---

# 十三、当前第一版建议页面能力

第一版建议做到：

- 顶部概览区
- 当前价格与 24h 状态
- 价格趋势图
- 成交量图
- 基础信息卡
- 链上状态卡
- AI 模板总结

不建议第一版做：

- 钱包连接
- 站内交易
- holders 排行
- 深度链上统计
- 复杂 K 线交易面板

---

# 十四、一句话总结

Token 详情页应规划为一个轻量级 Token Browser 页面。  
第一版应以 YAML 静态配置、Binance 当前行情、Binance Kline 图表、MongoDB 价格缓存和现有 RPC 状态服务为主要数据来源；前端通过详情主接口、图表接口和刷新接口完成页面渲染与局部更新。
