# AI + MCP 智能交互窗口设计文档

## 一、文档目标

本文档用于规划平台中的 **AI + MCP 智能交互窗口**。该页面不是普通聊天窗口，而是一个能够通过自然语言调用平台已有数据能力的智能交互工作台。

当前平台已完成的能力包括 Token 总览与详情、Token 图表、DAO 总览、Proposal 列表与详情、相似 Proposal 推荐、MongoDB 数据存储、Milvus 向量检索和 Snapshot Proposal 数据处理。

AI + MCP 窗口的目标是把这些能力统一封装为智能交互入口，让用户可以通过自然语言完成查询、分析和总结。

---

## 二、页面定位

AI + MCP 页面建议定位为：

> 面向区块链数据、DAO 治理数据和 Proposal 语义检索的智能分析助手。

核心职责：

1. 接收用户自然语言问题。
2. 判断用户意图。
3. 调用对应 MCP 工具或后端能力。
4. 整合结构化结果。
5. 生成自然语言回答。
6. 展示工具调用过程和数据来源。

该页面需要重点体现 AI 不只是聊天，而是能够调用真实系统能力；MCP 工具调用过程可解释；回答内容有数据来源支撑；Token、DAO、Proposal 三类能力可以统一交互。

---

## 三、整体页面结构

推荐采用三栏式布局：

```text
AI MCP Workspace
├── 左侧：推荐问题与功能入口
├── 中间：AI 对话主窗口
└── 右侧：MCP 工具调用与上下文面板
```

第一版也可以先做两栏：

```text
AI MCP Workspace
├── 中间：AI 对话主窗口
└── 右侧：工具调用与数据来源面板
```

从毕设展示效果来看，三栏式更能体现系统完整性。

---

## 四、页面模块总览

建议页面包含以下模块：

1. 顶部标题与模式切换区
2. 左侧推荐问题区
3. 中间 AI 对话区
4. 输入框与发送区
5. 右侧 MCP 工具调用记录区
6. 右侧上下文与数据来源区
7. 结果卡片展示区
8. 会话状态与错误提示区

---

# 五、模块一：顶部标题与模式切换区

## 5.1 模块目标

顶部区域用于展示当前页面名称，并允许用户选择 AI 交互模式。

推荐标题：

> MCP 智能交互工作台

## 5.2 展示内容

| 元素 | 说明 |
|---|---|
| 页面标题 | 展示 AI + MCP 页面名称 |
| 页面简介 | 简要说明该页面可查询 Token、DAO、Proposal |
| 模式切换 | Auto / Token / DAO / Proposal |
| 清空会话按钮 | 清空当前对话记录 |
| 状态标识 | 显示 AI 服务是否可用 |

## 5.3 交互模式设计

### Auto 自动模式

默认模式。用户可以随意提问，由后端自动判断意图并选择工具。适合“BTC 最近 7 天走势怎么样？”、“Aave 最近有哪些提案？”等问题。

### Token 分析模式

专门处理 Token 相关问题，例如价格、走势、图表、成交量、链上状态等。

### DAO 治理模式

专门处理 DAO 和 Proposal 列表查询，例如当前支持哪些 DAO、Aave 最近有哪些 Proposal。

### Proposal 分析模式

专门处理单个 Proposal 详情、关键词和相似检索，例如总结这个 proposal、查找相似 proposal。

---

# 六、模块二：左侧推荐问题区

## 6.1 模块目标

推荐问题区用于降低用户使用门槛，让用户知道可以问什么。该区域在答辩展示中非常重要，因为它可以快速触发系统能力。

## 6.2 推荐问题分类

```text
推荐问题
├── Token 分析
├── DAO 治理
└── Proposal 分析
```

## 6.3 Token 分析推荐问题

- BTC 当前价格是多少？
- ETH 最近 7 天走势如何？
- DOGE 最近成交量是否活跃？
- AVAX 当前链上状态怎么样？
- LINK 的市场表现如何？
- 帮我总结一下 BTC 当前状态。

## 6.4 DAO 治理推荐问题

- 当前平台支持哪些 DAO？
- Aave 最近有哪些 Proposal？
- ENS 最近有哪些治理提案？
- Uniswap 最近有哪些 closed proposal？
- 哪个 DAO 当前 Proposal 数量最多？
- 查看 Aave 的最新提案。

## 6.5 Proposal 分析推荐问题

- 总结一个 Proposal 的核心内容。
- 查找和当前 Proposal 相似的提案。
- 这个 Proposal 的关键词是什么？
- 解释这个 Proposal 的投票结果。
- 这个 Proposal 是否已经向量化？
- 查看该 Proposal 的 Snapshot 原始链接。

## 6.6 交互方式

推荐问题点击后可以填入输入框，也可以直接发送。第一版建议点击后直接发送，演示效果更好。

---

# 七、模块三：AI 对话主窗口

## 7.1 模块目标

AI 对话主窗口是页面核心区域，用于展示用户问题和 AI 回答。

## 7.2 消息类型

| 消息类型 | 说明 |
|---|---|
| user | 用户发送的问题 |
| assistant | AI 返回的回答 |
| system | 系统提示或错误提示 |
| tool | 工具调用过程，可选展示 |

第一版可以只在主窗口展示 user 和 assistant，工具调用详情放到右侧面板。

## 7.3 用户消息展示

用户消息建议展示用户提问内容、发送时间和当前模式。

示例：

```text
用户：BTC 最近 7 天走势怎么样？
时间：2026-04-24 10:00
模式：Auto
```

## 7.4 AI 回复展示

AI 回复建议展示自然语言回答、简要结论、数据来源提示和风险提示。

示例：

```text
BTC 最近 7 天整体呈上涨趋势，区间涨幅约 4.58%。成交额保持较高水平，说明市场交易活跃度较强。当前价格接近区间高位，短期波动风险仍需注意。

数据来源：Binance Kline、Token 详情接口。
该内容仅基于平台数据生成，不构成投资建议。
```

## 7.5 加载状态

用户发送问题后，应展示“正在理解问题...”“正在调用 MCP 工具...”“正在生成回答...”等状态。

## 7.6 错误状态

错误场景包括无法识别问题、工具调用失败、Token 不存在、Proposal 不存在、AI 服务异常等。建议主窗口给出友好提示，并在右侧工具面板展示具体失败工具。

---

# 八、模块四：输入框与发送区

## 8.1 模块目标

输入框用于接收用户自然语言问题。

## 8.2 输入框功能

建议支持：

- 多行输入
- Enter 发送
- Shift + Enter 换行
- 发送按钮
- 清空按钮
- 输入为空时禁用发送

## 8.3 Placeholder 建议

```text
请输入你想查询的 Token、DAO 或 Proposal 问题...
```

或：

```text
例如：BTC 最近 7 天走势怎么样？
```

## 8.4 输入限制

第一版建议最大输入长度 500 字；空输入不可发送；连续发送时按钮禁用，等待上一次回答完成。

---

# 九、模块五：MCP 工具调用记录区

## 9.1 模块目标

这是最能体现 MCP 项目特色的区域。它用于展示 AI 在回答过程中调用了哪些工具、传入了什么参数、是否成功以及使用了哪些数据来源。

## 9.2 展示内容

示例：

```text
Used MCP Tools

1. get_token_detail
   input: { "symbol": "BTC" }
   status: success
   duration: 320ms
   source: binance, mongo

2. get_token_chart
   input: { "symbol": "BTC", "range": "7d", "interval": "1h" }
   status: success
   duration: 580ms
   source: binance_kline
```

## 9.3 工具调用字段设计

| 字段 | 说明 |
|---|---|
| tool_name | 工具名称 |
| description | 工具说明 |
| input | 工具输入参数 |
| status | success / failed |
| duration_ms | 调用耗时 |
| data_source | 数据来源 |
| error_message | 错误信息 |
| result_summary | 工具结果摘要 |

## 9.4 推荐工具调用数据结构

```json
{
  "tool_name": "get_token_chart",
  "description": "获取 Token 图表数据",
  "input": {
    "symbol": "BTC",
    "range": "7d",
    "interval": "1h"
  },
  "status": "success",
  "duration_ms": 580,
  "data_source": ["binance_kline"],
  "result_summary": "Returned 168 kline records."
}
```

---

# 十、模块六：上下文与数据来源区

## 10.1 模块目标

上下文区用于展示 AI 回答所依据的数据，让回答更可信。

## 10.2 Token 查询上下文

当用户查询 Token 时，右侧上下文可以展示 symbol、当前价格、24h 涨跌、图表范围、链上状态、数据来源。

示例：

```json
{
  "tokens": [
    {
      "symbol": "BTC",
      "price_display": "77598.75 USDT",
      "change_percent": 4.58,
      "chart_range": "7d",
      "source": ["binance", "binance_kline"]
    }
  ]
}
```

## 10.3 DAO 查询上下文

当用户查询 DAO 时，可以展示 space_id、DAO 名称、Proposal 数量和最近同步时间。

## 10.4 Proposal 查询上下文

当用户查询 Proposal 时，可以展示 proposal_id、标题、space_id、状态、关键词、是否向量化、相似度等。

---

# 十一、模块七：结果卡片展示区

## 11.1 模块目标

结果卡片用于将 AI 工具调用结果以结构化方式展示。第一版可选，第二版建议加入。

## 11.2 Token 结果卡片

适合 BTC 当前价格是多少、ETH 最近走势如何等问题。展示 Token logo、symbol、当前价格、24h 涨跌、查看详情按钮。

## 11.3 DAO 结果卡片

适合当前支持哪些 DAO、Aave 最近有哪些 proposal 等问题。展示 DAO 名称、space_id、proposal_count、查看 Proposal 按钮。

## 11.4 Proposal 结果卡片

适合 Aave 最近有哪些提案、找相似 Proposal 等问题。展示 title、state、space_id、created、keywords、查看详情按钮。

---

# 十二、AI + MCP 后端接口设计

## 12.1 主接口

前端建议只调用一个主接口：

```http
POST /api/ai/chat
```

## 12.2 请求体设计

```json
{
  "session_id": "session-001",
  "message": "BTC 最近 7 天走势怎么样？",
  "mode": "auto",
  "history": []
}
```

## 12.3 请求字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| session_id | string | 否 | 会话 ID |
| message | string | 是 | 用户问题 |
| mode | string | 否 | auto / token / dao / proposal |
| history | array | 否 | 历史对话 |

## 12.4 响应体设计

```json
{
  "session_id": "session-001",
  "answer": "BTC 最近 7 天整体呈上涨趋势，区间涨幅约 4.58%。",
  "used_tools": [
    {
      "tool_name": "get_token_detail",
      "description": "获取 Token 详情",
      "input": {
        "symbol": "BTC"
      },
      "status": "success",
      "duration_ms": 320,
      "data_source": ["binance", "mongo"],
      "result_summary": "Loaded BTC detail successfully."
    }
  ],
  "context": {
    "tokens": [
      {
        "symbol": "BTC",
        "price_display": "77598.75 USDT",
        "change_percent": 4.58
      }
    ],
    "daos": [],
    "proposals": []
  },
  "suggested_questions": [
    "BTC 最近成交量如何？",
    "查看 BTC 详情页",
    "ETH 最近 7 天走势如何？"
  ]
}
```

---

# 十三、推荐 Pydantic 模型设计

## 13.1 AI Chat 请求模型

```python
from pydantic import BaseModel, Field
from typing import Literal, Any


class AIChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class AIChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(..., min_length=1, max_length=500)
    mode: Literal["auto", "token", "dao", "proposal"] = "auto"
    history: list[AIChatMessage] = []
```

## 13.2 工具调用模型

```python
class AIToolCallRecord(BaseModel):
    tool_name: str
    description: str | None = None
    input: dict[str, Any] = {}
    status: Literal["success", "failed", "running", "skipped"] = "success"
    duration_ms: int | None = None
    data_source: list[str] = []
    error_message: str | None = None
    result_summary: str | None = None
```

## 13.3 上下文模型

```python
class AIContextToken(BaseModel):
    symbol: str
    price_display: str | None = None
    change_percent: float | None = None
    source: list[str] = []


class AIContextDao(BaseModel):
    space_id: str
    name: str | None = None
    proposal_count: int | None = None
    last_synced_at: str | None = None


class AIContextProposal(BaseModel):
    proposal_id: str
    title: str | None = None
    space_id: str | None = None
    state: str | None = None
    keywords: list[str] = []
    similarity_score: float | None = None
```

## 13.4 AI Chat 响应模型

```python
class AIChatContext(BaseModel):
    tokens: list[AIContextToken] = []
    daos: list[AIContextDao] = []
    proposals: list[AIContextProposal] = []


class AIChatResponse(BaseModel):
    session_id: str
    answer: str
    used_tools: list[AIToolCallRecord] = []
    context: AIChatContext | None = None
    suggested_questions: list[str] = []
```

---

# 十四、MCP 工具设计

## 14.1 Token 工具

| 工具名 | 功能 | 对应后端能力 |
|---|---|---|
| get_token_overview | 获取代币总览 | Token overview service |
| get_token_detail | 获取 Token 详情 | Token detail service |
| get_token_chart | 获取 Token 图表 | Token chart service |
| refresh_token_data | 刷新 Token 数据 | Token refresh service |
| summarize_token | 总结 Token 状态 | 模板 / LLM |

## 14.2 DAO 工具

| 工具名 | 功能 | 对应后端能力 |
|---|---|---|
| get_dao_spaces | 获取 DAO 列表 | DAO spaces service |
| list_proposals | 查询 Proposal 列表 | Proposal query service |
| get_proposal_detail | 获取 Proposal 详情 | Proposal detail service |
| search_similar_proposals | 搜索相似 Proposal | Milvus similarity service |
| summarize_proposal | 总结 Proposal | 模板 / LLM |

---

# 十五、第一版意图识别策略

第一版可以先不用复杂 LLM Agent，而是用规则路由。

## 15.1 Token 问题识别

如果用户问题包含 BTC、ETH、DOGE、AVAX、LINK、价格、走势、成交量、K线、图表等关键词，则优先进入 Token 工具链。

示例：

```text
BTC 最近 7 天走势怎么样？
```

调用：

- get_token_detail
- get_token_chart

## 15.2 DAO 问题识别

如果用户问题包含 DAO、Aave、Uniswap、ENS、proposal、提案、治理等关键词，则进入 DAO / Proposal 工具链。

示例：

```text
Aave 最近有哪些提案？
```

调用：

- list_proposals(space_id="aave.eth")

## 15.3 相似 Proposal 问题识别

如果用户问题包含相似、类似、similar、推荐、相关提案等关键词，则调用 search_similar_proposals。前提是用户提供 proposal_id，或当前会话上下文中已有 proposal_id。

---

# 十六、AI 回答生成策略

## 16.1 第一版：规则 + 模板生成

第一版建议使用模板生成回答，不必立刻接入 LLM。

优点：

- 稳定
- 不会幻觉
- 不需要额外 API 成本
- 更容易调试

示例模板：

```text
{symbol} 当前价格为 {price_display}。
最近 {range} 内价格变化为 {change_percent}%。
成交额为 {total_quote_volume}。
数据来源包括 {data_sources}。
该内容仅基于平台数据生成，不构成投资建议。
```

## 16.2 第二版：结构化数据 + LLM

第二版可以将工具调用结果整理成结构化输入，再传给大模型生成总结。要求模型不编造不存在的数据，不提供投资建议，必须基于输入数据回答，并输出固定结构。

---

# 十七、前端页面状态设计

## 17.1 状态类型

| 状态 | 说明 |
|---|---|
| idle | 初始状态 |
| loading | 正在请求 |
| tool_running | 工具调用中 |
| success | 请求成功 |
| error | 请求失败 |

## 17.2 空状态

初次进入页面时，可以显示：

```text
你可以询问 Token 走势、DAO 治理提案或相似 Proposal。
```

## 17.3 错误状态

示例：

```text
未能识别该问题，请尝试输入 Token 符号或 DAO 名称。
```

或：

```text
工具调用失败，请稍后重试。
```

---

# 十八、开发优先级

## 第一阶段：基础交互窗口

1. 页面布局
2. 左侧推荐问题
3. 中间聊天窗口
4. 输入框
5. 右侧工具调用记录
6. `/api/ai/chat` 接口

## 第二阶段：规则路由工具调用

1. Token 问题识别
2. DAO 问题识别
3. Proposal 问题识别
4. 返回 used_tools
5. 返回 context
6. 模板生成 answer

## 第三阶段：结果卡片与上下文增强

1. Token 卡片
2. DAO 卡片
3. Proposal 卡片
4. 相似 Proposal 卡片
5. 数据来源展示增强

## 第四阶段：真实 MCP + LLM

1. 封装 MCP tools
2. 接入 LLM
3. 让 LLM 自动选择工具
4. 支持多轮上下文
5. 支持流式输出

---

# 十九、推荐项目结构

后端建议：

```text
app/
├── api/
│   └── ai_chat.py
├── models/
│   └── ai_chat_models.py
├── services/
│   ├── ai_chat_service.py
│   ├── ai_intent_service.py
│   ├── ai_response_builder.py
│   └── mcp_tool_service.py
└── tools/
    ├── token_tools.py
    ├── dao_tools.py
    └── proposal_tools.py
```

前端建议：

```text
src/
├── pages/
│   └── AIAssistantPage.tsx
├── components/
│   ├── ChatWindow.tsx
│   ├── RecommendedQuestions.tsx
│   ├── ToolCallPanel.tsx
│   ├── ContextPanel.tsx
│   └── MessageBubble.tsx
└── api/
    └── aiApi.ts
```

---

# 二十、一句话总结

AI + MCP 智能交互窗口应设计成一个三栏式智能工作台：左侧提供推荐问题，中间承载自然语言对话，右侧展示 MCP 工具调用记录与数据来源。第一版建议使用规则路由调用已完成的 Token、DAO、Proposal 接口，并用模板生成回答；后续再升级为真正由 LLM 通过 MCP 自动选择工具并生成分析结果。
