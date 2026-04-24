# DAO 治理页面技术设计与接口文档

## 一、文档目标

本文档用于规划平台中 **DAO 治理页面** 的技术方案与接口设计。当前阶段保留以下四个核心功能：

1. DAO 总览 / 切换页
2. Proposal 列表
3. Proposal 详情页
4. 相似 Proposal 推荐

不包含站内直接投票、钱包连接、AI 解读接口、新闻抓取和复杂 DAO 统计分析。

当前目标是将已经完成的 Snapshot Proposal 抓取、MongoDB 入库、文本清洗、关键词提取、Milvus 向量检索等能力，通过接口与前端页面组织起来，形成一个完整的 DAO 治理信息展示模块。

---

## 二、模块定位

DAO 治理页面是平台中用于展示 DAO 治理数据的核心页面，主要承担以下职责：

- 展示平台当前支持的 DAO
- 展示指定 DAO 的最新 Proposal
- 查看单个 Proposal 的完整内容
- 根据语义向量检索推荐相似 Proposal

页面结构建议如下：

```text
DAO Governance Module
├── DAO 总览 / 切换页
├── Proposal 列表页
└── Proposal 详情页
    └── 相似 Proposal 推荐区
```

---

## 三、功能一：DAO 总览 / 切换页

### 3.1 页面目标

DAO 总览 / 切换页用于展示当前平台支持的 DAO，并允许用户切换不同 DAO 查看对应 Proposal。

当前阶段建议支持：

- Aave
- Uniswap
- ENS

后续可扩展 Lido、The Graph、Arbitrum、Optimism、Compound 等。

### 3.2 页面展示内容

每个 DAO 建议展示为一个卡片或 Tab 项，包含：

| 字段 | 说明 |
|---|---|
| DAO 名称 | 例如 Aave、Uniswap、ENS |
| space_id | Snapshot space 标识，例如 `aave.eth` |
| Logo | DAO 图标 |
| 简短描述 | DAO 简介 |
|              |                                      |
| 最近同步时间 | 最近一次抓取或更新时间 |
| 状态 | enabled / disabled |

### 3.3 数据来源

静态信息建议来自：

```text
configs/dao_spaces_config.yaml
```

包括：

- space_id
- name
- logo
- description
- enabled
- sort_order

动态信息来自 MongoDB 中 Proposal 数据：

- proposal_count
- latest_proposal_created
- last_synced_at

---

## 四、功能二：Proposal 列表

### 4.1 页面目标

Proposal 列表用于展示某个 DAO 下的 Proposal 数据，并支持基础筛选与分页。

### 4.2 页面展示内容

每条 Proposal 建议以卡片或表格行展示，字段包括：

| 字段 | 说明 |
|---|---|
| title | Proposal 标题 |
| space_name | DAO 名称 |
| space_id | DAO space 标识 |
| state | Proposal 状态 |
| author | 作者 |
| created | 创建时间 |
| start | 投票开始时间 |
| end | 投票结束时间 |
| scores_total | 总投票得分 |
| keywords | 提取关键词 |
| link | Snapshot 原始链接 |
| 操作 | 查看详情 |

### 4.3 筛选条件

第一版建议支持：

| 筛选项 | 说明 |
|---|---|
| space_id | 按 DAO 查询 |
| state | 按状态筛选，如 active / closed |
| keyword | 按标题或关键词搜索 |
| page | 当前页 |
| page_size | 每页数量 |

### 4.4 数据来源

主要来自 MongoDB 中已经入库的 Snapshot Proposal 数据。建议集合：

```text
snapshot_proposals
```

或你当前实际使用的 Proposal 存储集合。

### 4.5

可以实时地去snapshot获取更新的proposal。

---

## 五、功能三：Proposal 详情页

### 5.1 页面目标

Proposal 详情页用于展示单个 Proposal 的完整信息，包括基本信息、正文、投票选项、投票结果、关键词与原始链接。

### 5.2 页面区域

```text
Proposal Detail Page
├── 顶部基本信息区
├── 正文内容区
├── 投票信息区
├── 文本处理结果区
└── 外部链接区
```

### 5.3 顶部基本信息区

展示字段：

| 字段 | 说明 |
|---|---|
| title | Proposal 标题 |
| proposal_id | Proposal 唯一 ID |
| space_id | DAO space |
| space_name | DAO 名称 |
| author | 作者 |
| state | 状态 |
| created | 创建时间 |
| start | 投票开始时间 |
| end | 投票结束时间 |

### 5.4 正文内容区

展示字段：

| 字段 | 说明 |
|---|---|
| body | Proposal 正文 |
| discussion | discussion 链接或讨论内容 |
| cleaned_text | 清洗后的文本 |

`body` 和 `discussion` 可能为空，需要前端做好空状态展示。如果正文为空，可以展示标题、choices、状态等结构化 fallback 信息。

### 5.5 投票信息区

展示字段：

| 字段 | 说明 |
|---|---|
| choices | 投票选项 |
| scores | 各选项得分 |
| scores_total | 总得分 |
| scores_updated | 分数更新时间 |
| snapshot | Snapshot 区块高度或标识 |

### 5.6 文本处理结果区

展示字段：

| 字段 | 说明 |
|---|---|
| keywords | 提取关键词 |
| cleaned_text | 清洗后文本 |
| vectorized | 是否已向量化 |
| embedding_model | 使用的向量模型 |

### 5.7 外部链接区

展示字段：

| 字段 | 说明 |
|---|---|
| link | Snapshot 原始 Proposal 链接 |
| discussion | 外部讨论链接 |

---

## 六、功能四：相似 Proposal 推荐

### 6.1 页面目标

相似 Proposal 推荐用于在 Proposal 详情页中展示语义上相近的历史 Proposal。这是本模块的核心亮点之一，体现系统的文本向量化和语义检索能力。

### 6.2 推荐逻辑

```text
用户打开 Proposal 详情页
        ↓
获取当前 proposal_id
        ↓
读取当前 Proposal 的向量
        ↓
Milvus 检索相似向量
        ↓
返回相似 proposal_id 列表
        ↓
MongoDB 回查完整 Proposal 信息
        ↓
前端展示相似 Proposal 推荐
```

### 6.3 推荐结果展示字段

| 字段 | 说明 |
|---|---|
| proposal_id | 相似 Proposal ID |
| title | 标题 |
| space_id | DAO space |
| space_name | DAO 名称 |
| state | 状态 |
| created | 创建时间 |
| similarity_score | 相似度分数 |
| keywords | 关键词 |
| link | Snapshot 链接 |

### 6.4 数据来源

| 数据 | 来源 |
|---|---|
| 当前 Proposal | MongoDB |
| Proposal 向量 | Milvus |
| 相似 Proposal ID | Milvus 检索结果 |
| 相似 Proposal 详情 | MongoDB 回查 |

---

## 七、接口设计总览

当前阶段建议提供以下 4 个接口：

| 接口 | 方法 | 用途 |
|---|---|---|
| `/api/dao/spaces` | GET | 获取 DAO 总览列表 |
| `/api/dao/proposals/list` | POST | 获取 Proposal 列表 |
| `/api/dao/proposals/detail` | POST | 获取 Proposal 详情 |
| `/api/dao/proposals/similar` | POST | 获取相似 Proposal 推荐 |

建议除 DAO spaces 外，其余接口均使用 POST + JSON Body，方便后续扩展筛选条件。

---

# 八、接口一：获取 DAO 总览列表

## 8.1 接口信息

```http
GET /api/dao/spaces
```

## 8.2 接口用途

获取当前平台支持的 DAO 列表，用于 DAO 总览 / 切换页。

## 8.3 请求参数

当前阶段无必填参数。

可选参数：

| 参数 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| enabled_only | bool | true | 是否只返回启用的 DAO |

示例：

```http
GET /api/dao/spaces?enabled_only=true
```

## 8.4 响应结构

```json
{
  "total": 3,
  "spaces": [
    {
      "space_id": "aave.eth",
      "name": "Aave",
      "logo": "/assets/dao/aave.png",
      "description": "Aave DAO governance proposals.",
      "enabled": true,
      "proposal_count": 120,
      "last_synced_at": "2026-04-24T10:30:00Z",
      "latest_proposal_created": "2026-04-23T08:00:00Z"
    }
  ]
}
```

## 8.5 错误处理

系统异常：

```json
{
  "code": "DAO_SPACES_ERROR",
  "message": "Failed to load DAO spaces."
}
```

---

# 九、接口二：获取 Proposal 列表

## 9.1 接口信息

```http
POST /api/dao/proposals/list
```

## 9.2 接口用途

根据 DAO space、状态、关键词、分页参数查询 Proposal 列表。

## 9.3 请求体

```json
{
  "space_id": "aave.eth",
  "state": "closed",
  "keyword": "",
  "page": 1,
  "page_size": 20
}
```

## 9.4 请求字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| space_id | string | 否 | null | DAO space ID；为空时查询全部 |
| state | string | 否 | null | Proposal 状态，如 active / closed |
| keyword | string | 否 | "" | 标题或关键词搜索 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

## 9.5 响应结构

```json
{
  "total": 120,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "proposal_id": "0xabc...",
      "space_id": "aave.eth",
      "space_name": "Aave",
      "title": "Proposal title",
      "state": "closed",
      "author": "0x123...",
      "created": 1713868800,
      "start": 1713868800,
      "end": 1714214400,
      "scores_total": 123456.78,
      "keywords": ["risk", "parameter", "governance"],
      "link": "https://snapshot.box/#/s:aave.eth/proposal/0xabc..."
    }
  ]
}
```

## 9.6 错误处理

参数错误：

```json
{
  "code": "INVALID_REQUEST",
  "message": "Invalid proposal list request."
}
```

系统异常：

```json
{
  "code": "PROPOSAL_LIST_ERROR",
  "message": "Failed to load proposal list."
}
```

---

# 十、接口三：获取 Proposal 详情

## 10.1 接口信息

```http
POST /api/dao/proposals/detail
```

## 10.2 接口用途

根据 `proposal_id` 获取单个 Proposal 的完整详情。

## 10.3 请求体

```json
{
  "proposal_id": "0xabc..."
}
```

## 10.4 响应结构

```json
{
  "proposal_id": "0xabc...",
  "space_id": "aave.eth",
  "space_name": "Aave",
  "title": "Proposal title",
  "body": "Proposal body...",
  "discussion": "https://forum.example.com/...",
  "author": "0x123...",
  "state": "closed",
  "start": 1713868800,
  "end": 1714214400,
  "snapshot": "12345678",
  "choices": ["Yes", "No"],
  "scores": [1000.0, 200.0],
  "scores_total": 1200.0,
  "scores_updated": 1714214400,
  "created": 1713868800,
  "link": "https://snapshot.box/#/s:aave.eth/proposal/0xabc...",
  "source": "snapshot",
  "cleaned_text": "Cleaned proposal text...",
  "keywords": ["risk", "governance"],
  "vectorized": true,
  "embedding_model": "BAAI/bge-small-en-v1.5"
}
```

## 10.5 错误处理

参数缺失：

```json
{
  "code": "PROPOSAL_ID_REQUIRED",
  "message": "Field 'proposal_id' is required."
}
```

Proposal 不存在：

```json
{
  "code": "PROPOSAL_NOT_FOUND",
  "message": "Proposal not found."
}
```

系统异常：

```json
{
  "code": "PROPOSAL_DETAIL_ERROR",
  "message": "Failed to load proposal detail."
}
```

---

# 十一、接口四：获取相似 Proposal 推荐

## 11.1 接口信息

```http
POST /api/dao/proposals/similar
```

## 11.2 接口用途

根据当前 `proposal_id`，通过 Milvus 向量检索查找语义相似的 Proposal，并返回对应 Proposal 简要信息。

## 11.3 请求体

```json
{
  "proposal_id": "0xabc...",
  "top_k": 5
}
```

## 11.4 请求字段说明

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| proposal_id | string | 是 | - | 当前 Proposal ID |
| top_k | int | 否 | 5 | 返回相似 Proposal 数量 |

## 11.5 响应结构

```json
{
  "proposal_id": "0xabc...",
  "top_k": 5,
  "items": [
    {
      "proposal_id": "0xdef...",
      "space_id": "aave.eth",
      "space_name": "Aave",
      "title": "Similar proposal title",
      "state": "closed",
      "created": 1713868800,
      "similarity_score": 0.87,
      "keywords": ["risk", "parameter"],
      "link": "https://snapshot.box/#/s:aave.eth/proposal/0xdef..."
    }
  ]
}
```

## 11.6 后端处理流程

```text
接收 proposal_id
        ↓
从 MongoDB 查询当前 Proposal
        ↓
确认该 Proposal 已向量化
        ↓
从 Milvus 获取或检索向量
        ↓
执行 top_k 相似度检索
        ↓
过滤自身 proposal_id
        ↓
MongoDB 回查相似 Proposal 详情
        ↓
返回推荐列表
```

## 11.7 错误处理

参数缺失：

```json
{
  "code": "PROPOSAL_ID_REQUIRED",
  "message": "Field 'proposal_id' is required."
}
```

Proposal 不存在：

```json
{
  "code": "PROPOSAL_NOT_FOUND",
  "message": "Proposal not found."
}
```

Proposal 未向量化：

```json
{
  "code": "PROPOSAL_NOT_VECTORIZED",
  "message": "Proposal vector not found."
}
```

系统异常：

```json
{
  "code": "SIMILAR_PROPOSAL_ERROR",
  "message": "Failed to search similar proposals."
}
```

---

# 十二、推荐 Pydantic 请求模型

## 12.1 Proposal 列表请求模型

```python
from pydantic import BaseModel, Field


class ProposalListRequest(BaseModel):
    space_id: str | None = None
    state: str | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
```

## 12.2 Proposal 详情请求模型

```python
from pydantic import BaseModel, Field


class ProposalDetailRequest(BaseModel):
    proposal_id: str = Field(..., description="Snapshot proposal id")
```

## 12.3 相似 Proposal 请求模型

```python
from pydantic import BaseModel, Field


class SimilarProposalRequest(BaseModel):
    proposal_id: str = Field(..., description="Snapshot proposal id")
    top_k: int = Field(default=5, ge=1, le=20)
```

---

# 十三、推荐 Pydantic 响应模型

## 13.1 DAO Space Item

```python
class DaoSpaceItem(BaseModel):
    space_id: str
    name: str
    logo: str | None = None
    description: str | None = None
    enabled: bool = True
    proposal_count: int = 0
    last_synced_at: str | None = None
    latest_proposal_created: str | None = None
```

## 13.2 DAO Spaces Response

```python
class DaoSpacesResponse(BaseModel):
    total: int
    spaces: list[DaoSpaceItem]
```

## 13.3 Proposal List Item

```python
class ProposalListItem(BaseModel):
    proposal_id: str
    space_id: str
    space_name: str | None = None
    title: str
    state: str | None = None
    author: str | None = None
    created: int | None = None
    start: int | None = None
    end: int | None = None
    scores_total: float | None = None
    keywords: list[str] = []
    link: str | None = None
```

## 13.4 Proposal List Response

```python
class ProposalListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProposalListItem]
```

## 13.5 Proposal Detail Response

```python
class ProposalDetailResponse(BaseModel):
    proposal_id: str
    space_id: str
    space_name: str | None = None
    title: str
    body: str = ""
    discussion: str | None = None
    author: str | None = None
    state: str | None = None
    start: int | None = None
    end: int | None = None
    snapshot: str | None = None
    choices: list[str] = []
    scores: list[float] = []
    scores_total: float | None = None
    scores_updated: int | None = None
    created: int | None = None
    link: str | None = None
    source: str = "snapshot"
    cleaned_text: str | None = None
    keywords: list[str] = []
    vectorized: bool = False
    embedding_model: str | None = None
```

## 13.6 Similar Proposal Response

```python
class SimilarProposalItem(BaseModel):
    proposal_id: str
    space_id: str
    space_name: str | None = None
    title: str
    state: str | None = None
    created: int | None = None
    similarity_score: float | None = None
    keywords: list[str] = []
    link: str | None = None


class SimilarProposalResponse(BaseModel):
    proposal_id: str
    top_k: int
    items: list[SimilarProposalItem]
```

---

# 十四、后端服务建议

建议新增或整理服务层：

```text
app/services/dao_service.py
app/services/proposal_query_service.py
app/services/proposal_similarity_service.py
```

## 14.1 dao_service.py

负责：

- 读取 DAO 配置
- 统计 DAO proposal 数量
- 返回 DAO 总览列表

## 14.2 proposal_query_service.py

负责：

- Proposal 列表查询
- Proposal 详情查询
- MongoDB 条件过滤与分页

## 14.3 proposal_similarity_service.py

负责：

- 获取当前 Proposal 向量
- 调用 Milvus 检索
- MongoDB 回查相似 Proposal
- 返回相似推荐结果

---

# 十五、推荐项目结构

```text
app/
├── api/
│   └── dao.py
├── models/
│   └── dao_models.py
├── services/
│   ├── dao_service.py
│   ├── proposal_query_service.py
│   └── proposal_similarity_service.py
├── storage/
│   └── snapshot_storage.py
└── clients/
    ├── mongodb_client.py
    └── milvus_client.py

configs/
└── dao_spaces_config.yaml
```

---

# 十六、第一版实现优先级

## 第一优先级

1. DAO spaces 接口
2. Proposal list 接口
3. Proposal detail 接口

## 第二优先级

4. Similar proposal 接口
5. Proposal 详情页中展示推荐结果

## 第三优先级

6. 搜索筛选优化
7. DAO 统计增强
8. 跨 DAO 相似提案推荐

---

# 十七、一句话总结

DAO 治理页面第一版应围绕“DAO 切换、Proposal 列表、Proposal 详情、相似 Proposal 推荐”四个功能完成。后端接口以 MongoDB 中的 Proposal 数据为基础，以 Milvus 向量检索作为相似推荐能力来源，从而将 Snapshot 抓取、文本处理和向量检索能力完整展示到前端页面中。
