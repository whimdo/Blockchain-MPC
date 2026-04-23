# 三大页面前端设计方案与 API 对接说明

## 一、设计目标

本方案围绕平台三大核心页面展开：

- Dashboard
- DAO
- AI

目标是将现有后端能力转化为可展示、可交互、可扩展的前端产品形态。  
方案重点描述：

- 页面定位
- 页面结构
- 模块划分
- 交互流程
- API 对接方式

本方案不包含前端代码实现，仅作为产品设计与前后端联调说明。

---

## 二、整体前端信息架构

建议前端采用顶部导航或左侧导航的方式组织三个一级页面。

### 一级导航结构

1. Dashboard
2. DAO
3. AI

### 页面间关系

- Dashboard 负责展示区块链与币种概览
- DAO 负责展示治理提案与详情
- AI 负责提供智能问答与分析能力
- 三个页面之间通过“币种详情”“Proposal 详情”“AI 解读入口”形成联动闭环

---

## 三、Dashboard 页面设计

## 3.1 页面定位

Dashboard 作为平台首页，承担以下作用：

- 向用户展示平台支持的币种与区块链数据
- 形成系统第一印象
- 提供进入详情页与 AI 分析页的入口
- 展示系统当前运行状态与数据规模

---

## 3.2 页面结构

### 3.2.1 顶部全局搜索区

#### 功能目标
支持用户快速搜索币种、链名称、地址或 DAO 关键词。

#### 建议展示元素
- 搜索输入框
- 搜索按钮
- 推荐搜索标签（如 ETH / BTC / Aave / Uniswap）

#### 交互说明
- 用户输入关键词后发起全局搜索
- 返回结果可以按类型分类展示：
  - 币种
  - Proposal
  - 地址
  - DAO

#### API 对接
- `GET /api/search/global?q=关键词`

#### 返回数据建议
- `type`
- `id`
- `title`
- `symbol`
- `space_id`
- `link`

---

### 3.2.2 平台总览指标区

#### 功能目标
快速展示平台整体运行状态。

#### 建议指标
- 当前支持链数量
- 当前支持币种数量
- 当前已同步 Proposal 数量
- 当前向量库文档数量
- 数据最后更新时间

#### API 对接
- `GET /api/dashboard/stats`

#### 返回数据建议
- `chain_count`
- `token_count`
- `proposal_count`
- `vector_count`
- `last_updated_at`

---

### 3.2.3 币种 / 链总览列表区

#### 功能目标
展示主流币种与对应链的总览信息。

#### 建议展示字段
- 币种名称
- Symbol
- 所属链
- 当前价格
- 数据来源
- 最近更新时间
- 操作按钮（查看详情）

#### 展示形式建议
- 表格视图
- 卡片视图（二选一，或支持切换）

#### 交互说明
- 点击某一行或某一张卡片进入币种详情页

#### API 对接
- `GET /api/dashboard/overview`

#### 返回数据建议
每条记录包含：
- `symbol`
- `name`
- `chain`
- `price`
- `currency`
- `source`
- `updated_at`
- `detail_id`

---

### 3.2.4 快速入口区（可选）

#### 功能目标
引导用户快速进入高价值功能。

#### 建议入口
- 查看 Aave 最新 Proposal
- 查看 Uniswap 最新 Proposal
- 打开 AI 智能问答
- 搜索相似 Proposal

#### API 对接
该区域通常不需要额外接口，可复用其他模块接口。

---

## 3.3 Dashboard 详情页设计

### 3.3.1 页面定位
展示某个币种或链的详细信息。

### 3.3.2 页面模块

#### 基本信息模块
展示：
- 币种名称
- Symbol
- 链名称
- 当前价格
- 数据来源
- 更新时间

#### 链上信息模块
展示：
- 区块高度
- 原生资产信息
- 可扩展的地址查询入口

#### 关联信息模块（可扩展）
展示：
- 关联 DAO
- 最近相关 Proposal
- 用 AI 进行分析的入口按钮

---

## 3.4 Dashboard API 汇总

### 总览接口
- `GET /api/dashboard/overview`

### 统计接口
- `GET /api/dashboard/stats`

### 详情接口
- `GET /api/dashboard/detail?id=xxx`
或
- `GET /api/dashboard/detail?symbol=ETH`

### 搜索接口
- `GET /api/search/global?q=xxx`

---

## 四、DAO 页面设计

## 4.1 页面定位

DAO 页面作为平台的治理信息中心，承担以下作用：

- 展示主流 DAO 的 Proposal 列表
- 提供 Proposal 的详细内容与治理状态
- 提供相似 Proposal 检索与 AI 解读入口
- 作为治理语义分析能力的主要展示页面

---

## 4.2 DAO 页面范围建议

当前阶段建议聚焦三个治理质量较高的 DAO：

- Aave
- Uniswap
- ENS

如后续扩展，可加入：
- Lido
- The Graph
- Arbitrum

---

## 4.3 页面结构

### 4.3.1 顶部 DAO 切换区

#### 功能目标
允许用户在多个 DAO 之间切换。

#### 建议展示形式
- 标签页 Tab
- 下拉选择框（移动端可选）

#### 可选 DAO
- Aave
- Uniswap
- ENS

#### 交互说明
- 点击切换后重新请求对应 DAO 的 Proposal 列表

#### API 对接
- `GET /api/dao/proposals?space_id=xxx`

---

### 4.3.2 Proposal 列表区

#### 功能目标
展示某 DAO 当前或最近的 Proposal 列表。

#### 建议展示字段
- Proposal 标题
- 状态（active / closed）
- 创建时间
- 作者
- 投票总量
- 关键词
- 查看详情按钮

#### 展示形式建议
- 列表卡片
- 支持分页
- 支持加载更多

#### API 对接
- `GET /api/dao/proposals?space_id=uniswap&page=1&limit=20`
- 支持附加参数：
  - `state`
  - `sort`
  - `keyword`

#### 返回数据建议
每条 Proposal 包含：
- `proposal_id`
- `space_id`
- `title`
- `state`
- `author`
- `created`
- `scores_total`
- `keywords`
- `link`

---

### 4.3.3 Proposal 筛选区

#### 功能目标
支持用户快速过滤 Proposal。

#### 建议筛选项
- 状态：
  - 全部
  - active
  - closed
- 排序：
  - 最新优先
  - 得票高优先
- 关键词搜索

#### API 对接
- `GET /api/dao/proposals?space_id=xxx&state=closed&keyword=fee&sort=created_desc`

---

### 4.3.4 Proposal 详情页

#### 页面定位
展示单个 Proposal 的完整信息及语义分析能力。

#### 模块划分

##### 基本信息模块
展示：
- 标题
- Proposal ID
- DAO 名称
- 作者
- 状态
- 创建时间
- 开始时间
- 结束时间

##### 正文内容模块
展示：
- Body
- Discussion
- 原始链接

##### 治理信息模块
展示：
- Choices
- Scores
- Scores Total

##### 语义信息模块
展示：
- 提取关键词
- 文本摘要（可选）
- 相似 Proposal 推荐

##### 操作模块
展示按钮：
- 前往 Snapshot 原页面
- 用 AI 解读此 Proposal

#### API 对接

##### 获取 Proposal 详情
- `GET /api/dao/proposal/detail?proposal_id=xxx`

##### 获取相似 Proposal
- `GET /api/dao/proposal/similar?proposal_id=xxx&top_k=5`

##### AI 解读入口
- `POST /api/ai/explain-proposal`

---

### 4.3.5 投票入口设计

#### 目标
为用户提供参与治理的入口。

#### 推荐实现方式
当前阶段建议：
- 页面展示“前往投票”按钮
- 跳转至 Snapshot 原始 Proposal 页面

#### 不建议当前阶段实现
- 站内直接投票
- 钱包签名投票
- 投票交易构造

#### 原因
- 实现复杂度高
- 与当前毕设主线关系较弱
- 风险和工作量明显高于展示跳转方案

---

## 4.4 DAO API 汇总

### Proposal 列表
- `GET /api/dao/proposals`

### Proposal 详情
- `GET /api/dao/proposal/detail`

### 相似 Proposal
- `GET /api/dao/proposal/similar`

### DAO 最新 Proposal
- `GET /api/dao/latest?space_id=xxx`

---

## 五、AI 页面设计

## 5.1 页面定位

AI 页面是整个平台的核心能力展示页。  
其核心目标不是单纯聊天，而是：

> 通过 MCP 调用平台已有能力，实现区块链数据与 DAO 治理信息的智能问答与分析。

---

## 5.2 页面结构

### 5.2.1 聊天主区域

#### 功能目标
承载用户输入问题与系统返回回答。

#### 页面元素
- 消息历史区
- 用户输入框
- 发送按钮
- 加载状态提示

#### 交互说明
- 用户输入问题
- 后端通过 MCP 调用相关能力
- 前端展示回答内容

---

### 5.2.2 推荐问题区

#### 功能目标
降低首次使用门槛，提高演示效果。

#### 建议问题示例
- Aave 最近有哪些提案？
- 请总结一下 Uniswap 最新 Proposal 的核心内容
- ENS 最近的治理动态是什么？
- ETH 当前价格是多少？
- 找出和这个 Proposal 相似的历史提案

#### API 对接
- `GET /api/ai/suggestions`

---

### 5.2.3 右侧上下文面板（强烈推荐）

#### 功能目标
展示 AI 回答所使用的上下文与来源，增强系统可信度和可解释性。

#### 建议展示内容
- 命中的 Proposal 列表
- 涉及的 DAO 名称
- 涉及的币种 / 链
- 使用的工具名称（如 proposal_search / market_query）
- 数据来源链接

#### 返回方式建议
由 AI 聊天接口在响应中附带：
- `used_tools`
- `related_proposals`
- `related_tokens`
- `references`

---

## 5.3 AI 页面核心交互流程

### 标准流程

1. 用户输入自然语言问题
2. 前端调用 AI 聊天接口
3. 后端执行问题理解与 MCP 路由
4. 调用相关能力：
   - Proposal 检索
   - Proposal 详情读取
   - 市场数据查询
   - 链上数据查询
5. 后端整合结果并生成回答
6. 前端展示回答与引用来源

---

## 5.4 支持的问题类型

### 1. DAO 治理类
- Aave 最近有哪些提案？
- Uniswap 最新 Proposal 是什么？
- ENS 最近通过了哪些治理决议？

### 2. Proposal 分析类
- 解释一下这个 Proposal 的含义
- 找出和这个 Proposal 相似的历史提案
- 这条 Proposal 的核心关键词是什么？

### 3. 市场与链上数据类
- ETH 当前价格是多少？
- 当前支持哪些币种？
- 这个币种在哪些链上支持？

### 4. 综合分析类
- Aave 最近的治理变化和市场表现有什么关系？
- 哪些 DAO 最近的治理最活跃？

---

## 5.5 AI API 对接方案

### AI 聊天接口
- `POST /api/ai/chat`

#### 请求体建议
- `question`
- `history`（可选）
- `session_id`（可选）

#### 返回体建议
- `answer`
- `used_tools`
- `related_proposals`
- `related_tokens`
- `references`

---

### 推荐问题接口
- `GET /api/ai/suggestions`

---

### Proposal 解读接口
- `POST /api/ai/explain-proposal`

#### 请求体建议
- `proposal_id`

#### 返回建议
- `summary`
- `keywords`
- `risk_points`
- `related_proposals`

---

## 六、三大页面之间的联动设计

## 6.1 Dashboard → AI
在币种详情页提供：
- “用 AI 分析此币种”入口

---

## 6.2 DAO → AI
在 Proposal 详情页提供：
- “用 AI 解读该 Proposal”入口

---

## 6.3 AI → DAO / Dashboard
AI 回答中如果提到：
- Proposal
- DAO
- 币种
- 链

应可提供跳转：
- 进入 Proposal 详情页
- 进入 Dashboard 详情页

---

## 七、前后端接口汇总

### Dashboard
- `GET /api/dashboard/overview`
- `GET /api/dashboard/stats`
- `GET /api/dashboard/detail`
- `GET /api/search/global`

### DAO
- `GET /api/dao/proposals`
- `GET /api/dao/proposal/detail`
- `GET /api/dao/proposal/similar`
- `GET /api/dao/latest`

### AI
- `POST /api/ai/chat`
- `GET /api/ai/suggestions`
- `POST /api/ai/explain-proposal`

---

## 八、实现优先级建议

## 第一优先级
1. Dashboard 总览页
2. DAO Proposal 列表页
3. Proposal 详情页

---

## 第二优先级
4. AI 问答页
5. 页面联动（AI 与 Proposal / Dashboard 的跳转）

---

## 第三优先级
6. 筛选与搜索优化
7. 推荐问题优化
8. 更丰富的可视化展示

---

## 九、最小可交付版本（MVP）

### Dashboard
- 币种总览
- 详情页
- 搜索入口

### DAO
- DAO 标签切换
- Proposal 列表
- Proposal 详情
- 跳转 Snapshot

### AI
- 问答输入框
- 返回回答
- 展示相关 Proposal

---

## 十、一句话总结

本方案将平台前端划分为 Dashboard、DAO 和 AI 三大页面：  
Dashboard 聚焦区块链与币种总览，DAO 聚焦治理提案展示与检索，AI 聚焦 MCP 驱动的智能问答。  
三者通过币种详情、Proposal 详情和 AI 分析入口形成闭环，最终构成一个可展示、可检索、可交互的区块链智能平台。
