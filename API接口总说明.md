# API 接口总说明

本文档覆盖 `app/api` 目录下当前业务接口文件：

```text
app/api/auth.py
app/api/ai_chat.py
app/api/dashboard_tokens.py
app/api/token_detail.py
app/api/dao_proposal.py
```

说明：`app/api/auth_dependencies.py` 是鉴权依赖工具文件，不直接暴露 HTTP 接口。

当前应用入口：`app/main.py`

```text
uvicorn app.main:app --reload
```

通用错误响应：

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message."
}
```

---

## 1. Auth 用户认证接口

基础前缀：

```text
/api/auth
```

### 1.1 注册用户

```http
POST /api/auth/register
```

功能：创建用户，使用 PBKDF2-HMAC-SHA256 加盐存储密码，并返回 JWT access token。

请求体：

```json
{
  "username": "alice",
  "password": "password123",
  "email": "alice@example.com",
  "display_name": "Alice"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | string | 是 | 3-32 位，只允许字母、数字、下划线；后端会转小写 |
| password | string | 是 | 8-128 位 |
| email | string/null | 否 | 邮箱，最长 128 位；后端会转小写 |
| display_name | string/null | 否 | 展示名，最长 64 位 |

成功响应：

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "user_id": "user-xxx",
    "username": "alice",
    "email": "alice@example.com",
    "display_name": "Alice",
    "status": "active",
    "created_at": "2026-04-25T10:00:00Z",
    "updated_at": "2026-04-25T10:00:00Z",
    "last_login_at": "2026-04-25T10:00:00Z"
  }
}
```

常见错误：

```json
{
  "code": "USER_ALREADY_EXISTS",
  "message": "Username or email already exists."
}
```

curl：

```bash
curl --location 'http://127.0.0.1:8000/api/auth/register' \
--header 'Content-Type: application/json' \
--data '{
  "username": "alice",
  "password": "password123",
  "email": "alice@example.com",
  "display_name": "Alice"
}'
```

### 1.2 登录

```http
POST /api/auth/login
```

功能：通过用户名或邮箱 + 密码登录，返回 JWT access token。

请求体：

```json
{
  "username": "alice",
  "password": "password123"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| username | string | 是 | 用户名或邮箱 |
| password | string | 是 | 密码 |

成功响应：同注册接口。

常见错误：

```json
{
  "code": "INVALID_CREDENTIALS",
  "message": "Invalid username or password."
}
```

curl：

```bash
curl --location 'http://127.0.0.1:8000/api/auth/login' \
--header 'Content-Type: application/json' \
--data '{
  "username": "alice",
  "password": "password123"
}'
```

### 1.3 获取当前用户

```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

功能：根据 Authorization Header 中的 JWT 获取当前用户信息。

请求头：

| Header | 必填 | 示例 |
|---|---|---|
| Authorization | 是 | `Bearer eyJhbGciOi...` |

成功响应：

```json
{
  "user": {
    "user_id": "user-xxx",
    "username": "alice",
    "email": "alice@example.com",
    "display_name": "Alice",
    "status": "active",
    "created_at": "2026-04-25T10:00:00Z",
    "updated_at": "2026-04-25T10:00:00Z",
    "last_login_at": "2026-04-25T10:00:00Z"
  }
}
```

常见错误：

```json
{
  "code": "INVALID_AUTHORIZATION_HEADER",
  "message": "Authorization header must be Bearer token."
}
```

curl：

```bash
curl --location 'http://127.0.0.1:8000/api/auth/me' \
--header 'Authorization: Bearer <access_token>'
```

---

## 2. AIChat 智能助手接口

基础前缀：

```text
/api/ai
```

### 2.1 发送聊天消息

```http
POST /api/ai/chat
```

功能：发送用户问题；后端会创建或读取会话，保存 user message，通过 MCP tools 生成回答，保存 assistant message、tool_calls、context。

请求体：

```json
{
  "session_id": null,
  "message": "当前平台支持哪些 DAO？",
  "mode": "dao",
  "history": [],
  "user_id": "user-xxx",
  "client": "web"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| session_id | string/null | 否 | 已有会话 ID；为空时自动创建 |
| message | string | 是 | 用户问题，1-500 字符 |
| mode | string | 否 | `auto` / `token` / `dao` / `proposal` |
| history | array | 否 | 历史消息；当前主要读取 Mongo session history |
| user_id | string/null | 否 | 用户 ID，用于把 session 归属到用户 |
| client | string/null | 否 | 客户端标识，默认 `web` |

成功响应：

```json
{
  "session_id": "session-xxx",
  "answer": "当前平台支持 ...",
  "mode": "dao",
  "status": "success",
  "used_tools": [],
  "context": {
    "tokens": [],
    "daos": [],
    "proposals": []
  },
  "result_cards": [],
  "suggested_questions": [],
  "error_message": null
}
```

curl：

```bash
curl --location 'http://127.0.0.1:8000/api/ai/chat' \
--header 'Content-Type: application/json' \
--data '{
  "session_id": null,
  "message": "当前平台支持哪些 DAO？",
  "mode": "dao",
  "history": [],
  "user_id": "user-xxx",
  "client": "web"
}'
```

### 2.2 创建聊天会话

```http
POST /api/ai/sessions
```

功能：创建一个空 AI 聊天窗口。

请求体：

```json
{
  "title": "BTC 分析",
  "mode": "auto",
  "user_id": "user-xxx",
  "client": "web"
}
```

响应：返回完整 `AIChatSessionDocument`。

### 2.3 获取聊天会话列表

```http
GET /api/ai/sessions?page=1&page_size=20&status=active&user_id=user-xxx
```

功能：分页获取聊天会话列表。

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page | int | 否 | 默认 1 |
| page_size | int | 否 | 默认 20，最大 100 |
| status | string | 否 | `active` / `archived` / `deleted` |
| user_id | string | 否 | 按用户过滤；不传时返回所有用户的非 deleted 会话 |

响应：

```json
{
  "page": 1,
  "page_size": 20,
  "total": 1,
  "sessions": [
    {
      "session_id": "session-xxx",
      "title": "BTC 分析",
      "mode": "auto",
      "status": "active",
      "created_at": "2026-04-25T10:00:00Z",
      "updated_at": "2026-04-25T10:05:00Z",
      "message_count": 2,
      "last_message": "当前平台支持..."
    }
  ]
}
```

### 2.4 获取会话详情

```http
GET /api/ai/sessions/{session_id}
```

功能：获取某个会话完整文档，包括 messages、tool_calls、context、suggested_questions。

响应：返回完整 `AIChatSessionDocument`。

### 2.5 更新会话

```http
PATCH /api/ai/sessions/{session_id}
```

功能：更新会话标题或状态。

请求体：

```json
{
  "title": "新的标题",
  "status": "archived"
}
```

响应：返回更新后的完整 `AIChatSessionDocument`。

### 2.6 删除会话

```http
DELETE /api/ai/sessions/{session_id}
```

功能：软删除会话，即把 `status` 更新为 `deleted`。

响应：返回更新后的完整 `AIChatSessionDocument`。

---

## 3. Dashboard Token 总览接口

基础前缀：

```text
/api/dashboard/tokens
```

### 3.1 获取 Dashboard Token 总览

```http
GET /api/dashboard/tokens/overview
```

功能：获取 Dashboard 页面展示的 Token 分组、卡片、价格和状态。

响应：

```json
{
  "page_updated_at": "2026-04-25T10:00:00Z",
  "total_tokens": 2,
  "group_count": 1,
  "groups": [
    {
      "group_name": "Main",
      "group_key": "main",
      "cards": [
        {
          "symbol": "BTC",
          "name": "Bitcoin",
          "display_name": "Bitcoin",
          "primary_chain": "bitcoin",
          "category": "Layer1",
          "logo": "/assets/tokens/btc.png",
          "price": 60000.0,
          "price_display": "60000.00 USDT",
          "updated_at": "2026-04-25T10:00:00Z",
          "status": "online",
          "tags": []
        }
      ]
    }
  ]
}
```

### 3.2 刷新全部 Dashboard Token

```http
POST /api/dashboard/tokens/refresh/all
```

功能：刷新全部 Dashboard Token 卡片价格数据。

响应结构同总览接口，返回 `TokenRefreshAllResponse`。

### 3.3 刷新单个 Dashboard Token

```http
POST /api/dashboard/tokens/refresh
```

请求体：

```json
{
  "symbol": "BTC"
}
```

功能：刷新单个 Token 卡片。

响应：返回单个 `TokenCard`。

常见错误：

```json
{
  "code": "TOKEN_NOT_FOUND",
  "message": "Token configuration not found."
}
```

---

## 4. Token 详情与 AI 摘要接口

基础前缀：

```text
/api/dashboard/tokens
```

### 4.1 获取 Token 详情

```http
POST /api/dashboard/tokens/detail
```

请求体：

```json
{
  "symbol": "BTC",
  "include_chart": true,
  "chart_range": "7d",
  "chart_interval": "1d",
  "chart_source": "binance"
}
```

字段说明：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| symbol | string | 是 | Token 符号 |
| include_chart | bool | 否 | 是否附带图表，默认 true |
| chart_range | string | 否 | `1d` / `7d` / `1m` / `3m` / `1y` |
| chart_interval | string/null | 否 | `15m` / `1h` / `4h` / `1d` / `1w` |
| chart_source | string | 否 | `binance` / `coingecko` / `mongo` |

响应：

```json
{
  "info": {
    "symbol": "BTC",
    "name": "Bitcoin",
    "display_name": "Bitcoin",
    "logo": "...",
    "primary_chain": "bitcoin",
    "category": "Layer1",
    "tags": [],
    "price_display": "60000.00 USDT",
    "price_change_24h": 1.2,
    "high_24h": 61000.0,
    "low_24h": 59000.0,
    "volume_24h": 1000000.0,
    "updated_at": "2026-04-25T10:00:00Z",
    "status": "online"
  },
  "chart": null
}
```

### 4.2 获取 Token 图表

```http
POST /api/dashboard/tokens/chart
```

请求体：

```json
{
  "symbol": "BTC",
  "range": "7d",
  "interval": "1h",
  "source": "binance"
}
```

响应：

```json
{
  "symbol": "BTC",
  "price_symbol": "BTCUSDT",
  "range": "7d",
  "interval": "1h",
  "source": "binance",
  "klines": [],
  "summary": {
    "start_price": 59000.0,
    "end_price": 60000.0,
    "change": 1000.0,
    "change_percent": 1.69,
    "high": 61000.0,
    "low": 58000.0,
    "total_quote_volume": 123456.0,
    "total_trades": 1234
  }
}
```

### 4.3 获取 Token AI 摘要

```http
POST /api/dashboard/tokens/ai-summary
```

请求体：

```json
{
  "symbol": "BTC",
  "chart_summary": {
    "start_price": 59000.0,
    "end_price": 60000.0,
    "change": 1000.0,
    "change_percent": 1.69,
    "high": 61000.0,
    "low": 58000.0,
    "total_quote_volume": 123456.0,
    "total_trades": 1234
  }
}
```

说明：`chart_summary` 可为空；为空时后端会先获取默认 7d 图表摘要。

响应：

```json
{
  "symbol": "BTC",
  "summary": {
    "symbol": "BTC",
    "title": "BTC Market Summary",
    "summary": "...",
    "key_points": [],
    "risk_notes": [],
    "generated_by": "template",
    "generated_at": "2026-04-25T10:00:00Z"
  }
}
```

---

## 5. DAO 与 Proposal 接口

基础前缀：

```text
/api/dao
```

### 5.1 获取 DAO 总览

```http
GET /api/dao/overview
```

功能：获取当前平台配置并可见的 DAO 列表，以及同步到本地的 proposal 数量。

响应：

```json
{
  "page_updated_at": "2026-04-25T10:00:00Z",
  "dao_count": 1,
  "daos": [
    {
      "name": "Aave",
      "space_id": "aave.eth",
      "logo": "...",
      "description": "...",
      "tags": [],
      "enabled": true,
      "latest_synchronization_time": "2026-04-25T10:00:00Z",
      "synchronized_proposals_count": 100
    }
  ]
}
```

### 5.2 获取某个 DAO 的 Proposal 列表

```http
GET /api/dao/{space_id}/proposals?page=1&page_size=20
```

路径参数：

| 参数 | 说明 |
|---|---|
| space_id | Snapshot DAO space id，例如 `aave.eth` |

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| page | int | 否 | 默认 1 |
| page_size | int | 否 | 默认 20，最大 100 |

响应：

```json
{
  "page_updated_at": "2026-04-25T10:00:00Z",
  "space_id": "aave.eth",
  "dao_name": "Aave",
  "page": 1,
  "page_size": 20,
  "proposals": [
    {
      "proposal_id": "proposal-xxx",
      "space_id": "aave.eth",
      "author": "0x...",
      "title": "Proposal title",
      "state": "closed",
      "keywords": []
    }
  ]
}
```

### 5.3 获取 Proposal 详情和相似 Proposal

```http
GET /api/dao/proposal/{proposal_id}?top_k=2
```

路径参数：

| 参数 | 说明 |
|---|---|
| proposal_id | Proposal ID |

查询参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| top_k | int | 否 | 相似 proposal 数量，默认 2，范围 1-20 |

响应：

```json
{
  "proposal": {
    "proposal_id": "proposal-xxx",
    "space_id": "aave.eth",
    "title": "Proposal title",
    "body": "...",
    "author": "0x...",
    "state": "closed",
    "choices": [],
    "scores": [],
    "scores_total": 0,
    "created": 0,
    "link": "...",
    "keywords": []
  },
  "similar_proposals": {
    "proposal_id": "proposal-xxx",
    "space_id": "aave.eth",
    "top_k": 2,
    "similar_proposals": []
  }
}
```

### 5.4 动态同步最新 Proposal

```http
POST /api/dao/proposals/dynamic-sync
```

功能：从 Snapshot 动态获取某个 DAO 最新 proposal，并把新 proposal 推送到 Kafka，供后续向量化入库。

请求体：

```json
{
  "space_id": "aave.eth",
  "latest_k": 10
}
```

响应：

```json
{
  "fetched_count": 10,
  "new_count": 2,
  "proposals": [
    {
      "proposal_id": "proposal-xxx",
      "space_id": "aave.eth",
      "author": "0x...",
      "title": "Proposal title",
      "state": "active",
      "keywords": []
    }
  ]
}
```

---

## 6. 接口测试建议顺序

1. 启动服务：

```bash
uvicorn app.main:app --reload
```

2. 先测认证：

```text
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

3. 再测无需登录的业务接口：

```text
GET  /api/dashboard/tokens/overview
GET  /api/dao/overview
```

4. 再测 AIChat：

```text
POST /api/ai/chat
GET  /api/ai/sessions?user_id=user-xxx
```

5. 最后测依赖外部服务较多的接口：

```text
POST /api/dashboard/tokens/refresh/all
POST /api/dao/proposals/dynamic-sync
```
