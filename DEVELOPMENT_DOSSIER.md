# 垂直文档问答助手开发档案

> 文档版本：v0.1  
> 项目阶段：MVP 技术方案与开发基线  
> 目标：让开发者可以按本文档直接拆分任务、实现、联调和验收。

## 1. 项目概述

### 1.1 项目目标

构建一个面向垂直领域资料的文档问答助手。用户可以上传 PDF、Word 或 Markdown 文档，系统完成文本解析、段落切片、向量化与索引。用户提问后，系统检索最相关的 5 个片段，调用大模型生成回答，并在回答中展示可追溯来源。

### 1.2 MVP 范围

必须支持：

- 上传 `.pdf`、`.docx`、`.md` 文件。
- 解析文本并保留来源元数据。
- 按段落及长度限制进行切片。
- 调用 Embedding 接口并把向量写入 pgvector。
- 保留 Chroma 向量存储适配接口，但 MVP 默认不启用。
- 对用户问题执行 Top 5 向量检索。
- 调用大模型生成带来源标记的回答。
- 通过 SSE 流式输出回答。
- 记录解析、检索、生成耗时及 Token 使用量。
- 按可配置价格表计算调用成本。
- 提供简单的文档上传、文档列表和聊天页面。
- 使用 Docker Compose 一键启动。

暂不包含：

- 复杂用户、组织、权限和计费系统。
- OCR、扫描件识别和图片内容理解。
- 多轮查询改写和 Agent 工具调用。
- 知识图谱、混合检索重排序和模型微调。
- 超大规模、多区域和高可用部署。

### 1.3 默认技术决策

| 领域 | 选择 | 原因 |
| --- | --- | --- |
| 后端 | Python 3.12 + FastAPI | 异步 API、类型清晰、适合 AI 服务 |
| 前端 | Next.js + TypeScript | 快速实现上传、列表和流式聊天页面 |
| 主数据库 | PostgreSQL 16 | 保存文档、切片、会话和调用记录 |
| 向量库 | pgvector | 与业务数据共用数据库，减少 MVP 运维复杂度 |
| 任务队列 | Celery + Redis | 文档解析和向量化异步执行，支持重试 |
| ORM | SQLAlchemy 2.x + Alembic | 成熟的异步数据访问和迁移方案 |
| 大模型 | OpenAI Compatible API | `base_url`、`api_key`、模型名均可配置 |
| 流式协议 | SSE | 浏览器接入简单，满足单向 Token 推送 |
| 文件存储 | Docker Volume 本地文件系统 | MVP 简单可靠，后续可替换为 S3/MinIO |

生产环境可在不改动业务接口的前提下，把文件存储替换为对象存储，把向量存储适配器替换为 Chroma。

## 2. 用户与核心场景

### 2.1 用户角色

- 普通用户：上传资料、查看处理状态、提问并阅读带来源的回答。
- 管理员：配置模型、Embedding、价格表和系统限制。

### 2.2 核心用户流程

1. 用户进入首页。
2. 上传 PDF、DOCX 或 Markdown 文件。
3. 页面显示上传成功和索引状态。
4. 后台解析文档、切片并写入向量库。
5. 索引完成后，用户在聊天框输入问题。
6. 系统展示检索来源，同时流式输出回答。
7. 用户点击来源，查看原文件、页码、章节或段落位置。
8. 管理员通过日志查看耗时、Token 和成本。

## 3. 总体架构

```mermaid
flowchart LR
    U[Browser] --> W[Next.js Web]
    W -->|REST / SSE| A[FastAPI API]
    A --> P[(PostgreSQL + pgvector)]
    A --> R[(Redis)]
    A --> F[File Volume]
    R --> C[Celery Worker]
    C --> F
    C --> P
    A --> E[Embedding API]
    A --> L[LLM API]
    C --> E
```

### 3.1 服务边界

- `web`：上传、文档列表、聊天和来源展示。
- `api`：参数校验、文档记录、检索、Prompt 组装、流式响应和指标记录。
- `worker`：文本解析、切片、Embedding 和向量写入。
- `postgres`：业务数据、切片、向量和调用记录。
- `redis`：Celery Broker、任务状态和短期锁。
- `files`：上传文件的持久化卷。

### 3.2 关键设计原则

- 上传接口只负责保存文件和创建任务，不在 HTTP 请求中完成全部解析。
- 文档处理必须幂等，同一文件重复提交不能生成重复切片。
- 向量记录必须携带完整来源元数据，不能只存文本。
- 回答只能基于检索片段，引用编号由系统注入并由后端校验。
- 模型名、向量维度、价格和 Top K 必须配置化。
- 所有耗时和 Token 记录必须带 `request_id`、`document_id` 或 `conversation_id`。

## 4. 项目结构建议

```text
vertical-doc-qa/
├─ apps/
│  ├─ api/
│  │  ├─ app/
│  │  │  ├─ api/
│  │  │  ├─ core/
│  │  │  ├─ db/
│  │  │  ├─ models/
│  │  │  ├─ schemas/
│  │  │  ├─ services/
│  │  │  ├─ vectorstores/
│  │  │  └─ main.py
│  │  ├─ tests/
│  │  ├─ alembic/
│  │  ├─ pyproject.toml
│  │  └─ Dockerfile
│  └─ web/
│     ├─ app/
│     ├─ components/
│     ├─ lib/
│     ├─ package.json
│     └─ Dockerfile
├─ infra/
│  ├─ postgres/init.sql
│  └─ nginx/default.conf
├─ data/uploads/
├─ .env.example
├─ docker-compose.yml
└─ README.md
```

## 5. 文档处理流水线

### 5.1 上传校验

- 允许扩展名：`.pdf`、`.docx`、`.md`。
- 默认最大文件大小：50 MB。
- 校验 MIME、文件头或魔数，不能只信任扩展名。
- 文件名只作为展示字段，磁盘路径使用 UUID。
- 计算 SHA-256，用于去重和任务幂等。
- 创建 `documents` 记录，初始状态为 `uploaded`。

### 5.2 状态机

```text
uploaded -> parsing -> chunking -> embedding -> ready
                                      |-> failed
                                      |-> retrying
```

状态说明：

| 状态 | 含义 |
| --- | --- |
| `uploaded` | 文件已保存，任务待执行 |
| `parsing` | 正在提取文本 |
| `chunking` | 正在按段落切片 |
| `embedding` | 正在生成向量并写入向量库 |
| `ready` | 可被检索 |
| `retrying` | 失败后等待自动重试 |
| `failed` | 达到重试上限，需要人工处理 |

### 5.3 文本解析

- PDF：使用 PyMuPDF，按页提取文本，保留 `page_no`。
- DOCX：使用 `python-docx`，按段落提取，识别 Heading 级别作为章节。
- Markdown：解析标题层级和正文，保留章节路径。
- 统一换行、空白和控制字符。
- 合并被错误换行拆开的段落，但保留明确空行和标题边界。
- 不把页眉、页脚重复文本直接删除，先在解析报告中标记，后续通过去重规则处理。

每个文本块至少保留：

```json
{
  "text": "段落正文",
  "source_name": "manual.pdf",
  "page_no": 12,
  "section_path": ["第三章", "3.2 参数配置"],
  "paragraph_index": 4,
  "char_start": 1820,
  "char_end": 2056
}
```

### 5.4 段落切片规则

默认参数：

- 目标切片长度：500 tokens。
- 最大切片长度：800 tokens。
- 最小切片长度：100 tokens，文档末尾除外。
- 相邻切片重叠：80 tokens。
- Embedding 批次：64 条。

算法：

1. 先按标题、段落和列表项形成自然文本块。
2. 顺序合并相邻短段落，直到接近目标长度。
3. 单个段落超过最大长度时，优先按句号、分号、换行切分。
4. 单个句子仍超长时，按字符窗口切分。
5. 为每个切片写入前一切片末尾的重叠文本。
6. 生成稳定的 `chunk_index` 和 `content_hash`。

切片不得跨越不同文档。默认不允许跨越一级章节，避免来源语义被混合。

### 5.5 Embedding 与写入

- 调用批处理 Embedding 接口。
- 默认模型通过 `EMBEDDING_MODEL` 配置。
- `EMBEDDING_DIMENSION` 必须与数据库向量维度和模型输出一致。
- 每条切片先插入 PostgreSQL，再写向量，或通过事务统一提交。
- 写入向量使用 upsert，键为 `(document_id, chunk_index, content_hash)`。
- 接口失败采用指数退避重试，最多 5 次。
- 达到重试上限后把文档置为 `failed`，保存安全的错误摘要。
- 重建索引时复用切片，只重新计算 Embedding。

### 5.6 删除与重建

- 删除文档时，同时删除原文件、切片、向量、任务记录和缓存。
- 使用软删除标记 `deleted_at`，后台清理图片或外部资源。
- 支持 `POST /documents/{id}/reindex` 重建向量。
- 重建期间旧索引保持可检索，新索引完成后原子切换版本。

## 6. 检索与回答

### 6.1 检索流程

1. 对用户问题做长度和空值校验。
2. 调用 Embedding 生成查询向量。
3. 在 pgvector 中按余弦距离检索 Top 5。
4. 默认按 `knowledge_base_id` 和 `status=ready` 过滤。
5. 可按 `min_similarity` 阈值过滤。
6. 对相同文档相邻切片做轻量去重，避免来源集中度过高。
7. 返回文本、分数和完整来源元数据。

默认检索参数：

```yaml
top_k: 5
min_similarity: 0.25
max_chunks_per_document: 3
```

如果所有结果低于阈值，回答必须明确说明当前资料中没有足够依据，而不是让模型自行补充。

### 6.2 Prompt 约束

系统 Prompt 建议：

```text
你是一个严格的垂直领域文档问答助手。

规则：
1. 只能依据提供的资料片段回答。
2. 资料不足时明确说明，不得编造。
3. 每个关键结论后必须标注来源，例如 [S1]。
4. 不得生成未出现在片段中的引用编号。
5. 回答应简洁、准确，优先使用文档中的术语。
```

用户 Prompt 结构：

```text
问题：
{question}

资料：
[S1]
来源：manual.pdf，第 12 页，3.2 参数配置
内容：...

[S2]
...
```

### 6.3 引用处理

- 后端把检索结果映射为 `S1` 至 `S5`。
- 响应中的引用编号必须再次映射回真实 `chunk_id`。
- 对无效引用编号记录告警，但不把不存在的来源传给前端。
- 前端在来源卡片中展示文件名、页码、章节和命中分数。
- 点击来源可打开预览；MVP 可以先展示对应原文片段。

### 6.4 无答案策略

以下任一情况触发保守回答：

- 没有检索结果。
- 最高相似度低于阈值。
- 片段总 Token 超过上下文预算。
- 模型响应不包含任何有效引用。

保守回答示例：

```text
当前文档中没有找到足够依据回答这个问题。你可以补充相关文件，或换一种更具体的问法。
```

## 7. 流式输出协议

接口：`POST /api/v1/chat/stream`

请求：

```json
{
  "conversation_id": "optional-uuid",
  "question": "设备如何进入维护模式？",
  "knowledge_base_id": "default"
}
```

响应类型：`text/event-stream`

事件顺序：

```text
event: meta
data: {"request_id":"req_123","conversation_id":"conv_123"}

event: sources
data: {"sources":[{"id":"S1","chunk_id":"...","name":"manual.pdf","page":12,"section":"3.2 参数配置","score":0.83}]}

event: token
data: {"delta":"进入维护"}

event: usage
data: {"input_tokens":1832,"output_tokens":246,"embedding_tokens":35,"cost":0.0031,"currency":"USD"}

event: done
data: {"message_id":"msg_123","finish_reason":"stop","total_ms":2840}

event: error
data: {"code":"LLM_TIMEOUT","message":"模型响应超时","retryable":true}
```

实现要求：

- 客户端断开时，后端应停止继续生成并释放连接。
- `meta` 必须最先发送，便于日志串联。
- `sources` 应在首个 Token 前发送，让来源可立即展示。
- 流式接口不能缓存，响应头包含 `Cache-Control: no-cache`。
- Nginx 配置关闭代理缓冲并延长读超时。

## 8. API 设计

基础路径：`/api/v1`

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 存活检查 |
| `GET` | `/ready` | 数据库、Redis 和模型配置检查 |
| `POST` | `/documents` | 上传文档 |
| `GET` | `/documents` | 分页查询文档 |
| `GET` | `/documents/{id}` | 查看文档及处理状态 |
| `DELETE` | `/documents/{id}` | 删除文档和索引 |
| `POST` | `/documents/{id}/reindex` | 重建索引 |
| `POST` | `/chat/stream` | 检索并流式回答 |
| `GET` | `/conversations/{id}` | 查看会话历史 |
| `GET` | `/metrics/calls` | 查询调用耗时和 Token 成本 |

### 8.1 上传文档

请求：

```http
POST /api/v1/documents
Content-Type: multipart/form-data
```

字段：

- `file`：必填。
- `knowledge_base_id`：可选，默认 `default`。
- `title`：可选，默认使用文件名。

响应：

```json
{
  "id": "b263f5fd-2407-4b14-b21d-8a69e3744cf7",
  "title": "设备维护手册",
  "file_name": "manual.pdf",
  "status": "uploaded",
  "duplicate": false,
  "created_at": "2026-09-16T10:00:00Z"
}
```

错误：

| HTTP | 错误码 | 场景 |
| --- | --- | --- |
| `400` | `UNSUPPORTED_FILE_TYPE` | 文件类型不支持 |
| `413` | `FILE_TOO_LARGE` | 超过大小限制 |
| `422` | `INVALID_FILE` | 文件损坏或为空 |
| `409` | `DUPLICATE_CONTENT` | 不建议重复入库时可返回 |

### 8.2 文档列表

查询参数：

- `page`：默认 1。
- `page_size`：默认 20，最大 100。
- `status`：可选。
- `knowledge_base_id`：可选。

### 8.3 问答

`POST /chat/stream` 使用 SSE，不属于普通 JSON 响应。超时建议：

- 检索超时：10 秒。
- 首个 Token 超时：30 秒。
- 整个生成超时：120 秒。

## 9. 数据模型

### 9.1 documents

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 文档 ID |
| `knowledge_base_id` | VARCHAR(64) | 知识库标识 |
| `title` | VARCHAR(255) | 展示标题 |
| `file_name` | VARCHAR(255) | 原始文件名 |
| `file_ext` | VARCHAR(16) | 扩展名 |
| `mime_type` | VARCHAR(128) | MIME |
| `file_size` | BIGINT | 文件大小 |
| `storage_path` | TEXT | 本地或对象存储路径 |
| `sha256` | CHAR(64) | 内容哈希 |
| `status` | VARCHAR(32) | 处理状态 |
| `error_code` | VARCHAR(64) | 错误码 |
| `error_message` | TEXT | 安全错误摘要 |
| `chunk_count` | INTEGER | 切片数 |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | 更新时间 |
| `deleted_at` | TIMESTAMPTZ | 软删除时间 |

索引：

- 唯一索引：`(knowledge_base_id, sha256)`，如果不允许重复上传。
- 普通索引：`(knowledge_base_id, status, created_at)`。

### 9.2 document_chunks

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 切片 ID |
| `document_id` | UUID FK | 所属文档 |
| `knowledge_base_id` | VARCHAR(64) | 冗余过滤字段 |
| `chunk_index` | INTEGER | 文档内顺序 |
| `content` | TEXT | 切片正文 |
| `content_hash` | CHAR(64) | 内容哈希 |
| `token_count` | INTEGER | Token 数 |
| `page_no` | INTEGER | 页码，可空 |
| `section_path` | JSONB | 章节路径 |
| `paragraph_index` | INTEGER | 段落序号 |
| `char_start` | INTEGER | 原文字符起点 |
| `char_end` | INTEGER | 原文字符终点 |
| `embedding` | VECTOR(1536) | 文本向量 |
| `created_at` | TIMESTAMPTZ | 创建时间 |

索引：

- `(document_id, chunk_index)`。
- 对 `embedding` 建 HNSW 或 IVFFlat 索引。
- 对 `knowledge_base_id` 建过滤索引。

向量维度必须由环境变量控制，并在迁移中保持一致。切换不同维度的模型时，需要新增向量列或执行离线重建。

### 9.3 conversations

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 会话 ID |
| `knowledge_base_id` | VARCHAR(64) | 知识库 |
| `title` | VARCHAR(255) | 会话标题 |
| `created_at` | TIMESTAMPTZ | 创建时间 |
| `updated_at` | TIMESTAMPTZ | 更新时间 |

### 9.4 messages

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 消息 ID |
| `conversation_id` | UUID FK | 会话 |
| `role` | VARCHAR(16) | `user` 或 `assistant` |
| `content` | TEXT | 消息正文 |
| `status` | VARCHAR(16) | 完成、中断或失败 |
| `request_id` | UUID | 链路标识 |
| `created_at` | TIMESTAMPTZ | 创建时间 |

### 9.5 retrieval_events

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 记录 ID |
| `request_id` | UUID | 请求标识 |
| `message_id` | UUID | 助手消息 |
| `query` | TEXT | 用户问题 |
| `top_k` | INTEGER | 检索数量 |
| `chunk_ids` | JSONB | 命中切片 |
| `scores` | JSONB | 相似度 |
| `embedding_ms` | INTEGER | Embedding 耗时 |
| `search_ms` | INTEGER | 向量检索耗时 |
| `created_at` | TIMESTAMPTZ | 创建时间 |

### 9.6 llm_calls

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | UUID PK | 记录 ID |
| `request_id` | UUID | 请求标识 |
| `provider` | VARCHAR(64) | 模型供应商 |
| `model` | VARCHAR(128) | 模型名 |
| `operation` | VARCHAR(32) | `embedding` 或 `chat` |
| `input_tokens` | INTEGER | 输入 Token |
| `output_tokens` | INTEGER | 输出 Token |
| `cached_tokens` | INTEGER | 缓存命中 Token |
| `unit_price_input` | NUMERIC(18,8) | 输入单价 |
| `unit_price_output` | NUMERIC(18,8) | 输出单价 |
| `currency` | CHAR(3) | 币种 |
| `estimated_cost` | NUMERIC(18,8) | 估算成本 |
| `latency_ms` | INTEGER | 总耗时 |
| `first_token_ms` | INTEGER | 首 Token 耗时，可空 |
| `success` | BOOLEAN | 是否成功 |
| `error_code` | VARCHAR(64) | 错误码 |
| `created_at` | TIMESTAMPTZ | 创建时间 |

## 10. Token 与成本统计

### 10.1 统计范围

- Embedding：查询向量和文档向量生成。
- Chat 输入：System Prompt、问题、5 条上下文。
- Chat 输出：流式生成的全部 Token。
- 可选包含查询改写、重排序和摘要模型调用。

### 10.2 计算方式

```text
estimated_cost =
  input_tokens / 1,000,000 * input_price_per_million +
  output_tokens / 1,000,000 * output_price_per_million
```

要求：

- 优先使用供应商响应中的真实 usage。
- 流式响应无法取得 usage 时，使用 Tokenizer 估算并标记 `is_estimated=true`。
- 价格表配置化，不把易变化的价格写死在业务代码中。
- 保存调用发生时的价格快照，历史数据不受后续调价影响。
- 统计按请求、文档、知识库、日期和模型聚合。

建议补充字段：`is_estimated`、`price_version`。

## 11. 前端设计

### 11.1 页面范围

单页包含三个区域：

1. 左侧文档区：上传按钮、文档列表、处理状态、删除和重建入口。
2. 中间聊天区：历史消息、流式回答、停止生成按钮。
3. 来源面板：展示本次回答引用的文档、页码、章节、分数和原文片段。

### 11.2 交互要求

- 上传后立即出现在列表，并轮询或订阅状态。
- 状态使用明确的文字和图标，不能只使用颜色。
- 未完成索引的文档不能参与检索，或明确提示其尚未就绪。
- 流式输出期间显示停止按钮。
- 来源卡片与回答中的 `[S1]` 可相互定位。
- 请求失败显示可重试操作，并保留用户已输入问题。
- 长文件名、长章节名和长来源文本必须正确换行或截断。

### 11.3 状态管理

- 服务端数据：文档列表、会话历史、调用指标。
- 本地状态：输入框、上传进度、流式文本、当前来源。
- 流式响应使用 `fetch` 读取 `ReadableStream`，不要在 MVP 中引入复杂状态库。
- 请求中断时使用 `AbortController`。

## 12. 配置项

`.env.example` 至少包含：

```dotenv
APP_ENV=development
APP_API_KEY=

DATABASE_URL=postgresql+asyncpg://app:app@postgres:5432/docqa
REDIS_URL=redis://redis:6379/0
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_MB=50

LLM_BASE_URL=https://api.example.com/v1
LLM_API_KEY=replace-me
LLM_MODEL=provider-chat-model
EMBEDDING_BASE_URL=https://api.example.com/v1
EMBEDDING_API_KEY=replace-me
EMBEDDING_MODEL=provider-embedding-model
EMBEDDING_DIMENSION=1536

RETRIEVAL_TOP_K=5
RETRIEVAL_MIN_SIMILARITY=0.25
CHUNK_TARGET_TOKENS=500
CHUNK_MAX_TOKENS=800
CHUNK_OVERLAP_TOKENS=80

VECTOR_STORE=pgvector
CHROMA_URL=
LOG_LEVEL=INFO
```

密钥不得写入镜像、前端变量或 Git 仓库。

## 13. Docker 一键启动

`docker-compose.yml` 默认包含：

- `web`
- `api`
- `worker`
- `postgres`，使用带 pgvector 的镜像
- `redis`

启动命令：

```bash
docker compose up --build
```

启动要求：

- `postgres` 和 `redis` 配置健康检查。
- `api` 和 `worker` 等待数据库就绪后启动。
- API 启动前执行 Alembic 迁移，或使用独立 `migrate` 一次性服务。
- `uploads` 和 `pgdata` 使用命名卷持久化。
- 默认只暴露 Web 端口；数据库和 Redis 不映射到宿主机。
- 支持通过 `.env` 覆盖模型、密钥和端口。

建议端口：

| 服务 | 容器端口 | 宿主端口 |
| --- | --- | --- |
| web | 3000 | 3000 |
| api | 8000 | 8000 |
| postgres | 5432 | 不暴露 |
| redis | 6379 | 不暴露 |

## 14. 异常处理与可靠性

### 14.1 统一错误结构

```json
{
  "error": {
    "code": "DOCUMENT_PARSE_FAILED",
    "message": "文档解析失败",
    "request_id": "req_123",
    "retryable": false
  }
}
```

### 14.2 重试策略

- 文件存储错误：最多重试 3 次。
- Embedding 网络错误和限流：最多重试 5 次，指数退避。
- 数据库瞬时错误：最多重试 3 次。
- 文档解析错误：默认不自动重试，避免无效消耗。
- LLM 可重试错误：仅在尚未向客户端发送内容时重试。

### 14.3 超时

- 上传请求：60 秒。
- 文档解析：每 100 页 5 分钟，设置总上限。
- 单次 Embedding 批次：60 秒。
- 向量检索：10 秒。
- Chat 首 Token：30 秒。
- Chat 总生成：120 秒。

### 14.4 幂等与并发

- 使用 `sha256` 判断重复文档。
- Celery 任务以 `document_id + index_version` 作为幂等键。
- 同一文档同时只允许一个索引任务。
- 使用 Redis 锁避免重复重建。

## 15. 安全与隐私

- 文件上传限制类型、大小、数量和速率。
- 使用 UUID 作为存储路径，防止路径穿越。
- 用户问题、文档正文和模型回答默认不写入应用日志。
- 日志只记录 ID、长度、耗时和错误码。
- API Key 仅保存在服务端环境变量或密钥服务中。
- 若部署到公网，必须启用鉴权、TLS、CORS 白名单和请求限流。
- 删除文档时清理向量、缓存和原文件。
- 对 Prompt 注入做基础隔离：文档片段只作为资料，不执行其中指令。
- 大模型输出在前端按文本渲染，禁止直接插入不受信任 HTML。

## 16. 可观测性

### 16.1 链路指标

每次问答记录：

- `request_id`
- 查询 Embedding 耗时
- 向量检索耗时
- 上下文组装耗时
- LLM 首 Token 耗时
- LLM 总耗时
- 文档处理总耗时
- 输入、输出和 Embedding Token
- 估算费用
- 命中切片和相似度
- 是否触发无答案策略

### 16.2 日志

使用结构化 JSON 日志，核心字段：

```json
{
  "level": "INFO",
  "event": "chat.completed",
  "request_id": "req_123",
  "conversation_id": "conv_123",
  "model": "provider-chat-model",
  "retrieval_ms": 82,
  "first_token_ms": 640,
  "total_ms": 2840,
  "input_tokens": 1832,
  "output_tokens": 246,
  "estimated_cost": 0.0031
}
```

### 16.3 告警建议

- 文档处理失败率连续 10 分钟超过 10%。
- Chat 首 Token P95 超过 10 秒。
- Embedding 或 LLM 限流率超过 5%。
- 单请求成本超过配置阈值。
- 向量检索 P95 超过 1 秒。

## 17. 测试计划

### 17.1 单元测试

- 文件类型和大小校验。
- Markdown、DOCX、PDF 文本解析。
- 中英文段落切片和最大长度约束。
- 章节路径和页码元数据保留。
- Token 与成本计算。
- 引用编号映射和无效引用过滤。
- 无检索结果时的回答策略。

### 17.2 集成测试

- 上传文档到任务完成的状态流转。
- Embedding API 重试和失败回滚。
- pgvector 写入与 Top 5 检索。
- SSE 事件顺序和流式中断。
- 删除文档后向量不可检索。
- 重复上传和重复任务幂等。

### 17.3 端到端测试

准备三类固定资料：

- 带章节的中文 PDF 手册。
- 含标题层级的 DOCX。
- 多段落 Markdown 知识库。

至少验证：

1. 上传后能进入 `ready`。
2. 能检索出预期文档。
3. 回答包含有效来源编号。
4. 来源页码或章节可定位。
5. 无依据问题不会编造答案。
6. 数据库中存在对应耗时和 Token 记录。

### 17.4 验收指标

- 10 MB、100 页以内的文本型 PDF 在 5 分钟内完成索引。
- 问答首 Token P95 小于 5 秒，模型服务正常时。
- 20 个标准测试问题的来源命中率达到 90% 以上。
- 回答中的伪引用率为 0。
- 上传、解析、检索、生成的主要耗时均可查询。
- `docker compose up --build` 后无需手工建库即可访问页面。

## 18. 开发里程碑

### M0：工程骨架

- 创建前后端、数据库迁移、Redis 和 Docker Compose。
- 完成健康检查和基础 CI。
- 页面可访问，数据库可连接。

完成标准：一条命令启动全部服务。

### M1：文档入库

- 实现上传、文件校验、异步任务和状态轮询。
- 实现三类文档解析。
- 实现段落切片和元数据保存。

完成标准：测试文件能从 `uploaded` 进入 `embedding` 前的状态。

### M2：向量检索

- 接入 Embedding API。
- 实现 pgvector 存储、索引和 Top 5 检索。
- 实现向量库适配接口。

完成标准：给定标准问题，能稳定返回预期切片。

### M3：带来源问答

- 实现 Prompt 组装、引用映射和无答案策略。
- 实现会话和消息存储。

完成标准：回答能追溯到文档、页码和章节。

### M4：流式与成本

- 实现 SSE 流式输出和前端增量渲染。
- 记录耗时、Token 和成本。

完成标准：页面可连续显示 Token，调用记录完整。

### M5：部署与验收

- 完善 Docker 健康检查、迁移和持久化。
- 完成安全、异常和端到端测试。

完成标准：通过第 17.4 节验收指标。

## 19. 开发任务拆分

| 优先级 | 任务 | 产出 |
| --- | --- | --- |
| P0 | 工程脚手架 | API、Web、Worker、Compose |
| P0 | 数据库模型与迁移 | 六张核心表 |
| P0 | 上传与状态机 | 文档 API 和处理任务 |
| P0 | 三种解析器 | PDF、DOCX、Markdown |
| P0 | 段落切片 | 可测试的切片服务 |
| P0 | Embedding 适配器 | 批处理、重试、usage |
| P0 | pgvector 适配器 | 写入和 Top 5 查询 |
| P0 | 问答编排 | 检索、Prompt、引用 |
| P0 | SSE 接口 | 事件协议和中断 |
| P1 | 前端页面 | 上传、列表、聊天、来源 |
| P1 | 成本记录 | llm_calls 和聚合查询 |
| P1 | Docker 联调 | 一键启动 |
| P2 | Chroma 适配 | 可选实现 |
| P2 | 管理配置 | 模型和价格表界面 |

## 20. 完成定义

一个功能只有同时满足以下条件才算完成：

- 接口、数据结构和异常路径已实现。
- 至少覆盖正常路径、边界条件和失败重试测试。
- 日志中不泄露密钥、文档正文和用户隐私。
- 耗时、Token 和成本字段已落库。
- 前端状态和错误提示完整。
- 本地 Docker Compose 可复现。
- 文档和配置项已更新。

## 21. 后续演进

- 混合检索：向量检索 + PostgreSQL 全文检索。
- Reranker：对 Top 20 重排后输出 Top 5。
- 查询改写：结合会话上下文生成独立检索问题。
- OCR：支持扫描 PDF 和图片附件。
- 对象存储：接入 MinIO 或 S3。
- 文档权限：按用户、部门和知识库隔离。
- 引用预览：在浏览器中定位 PDF 页码或 Markdown 锚点。
- 成本预算：按用户、知识库和日限额控制调用。
- 评测体系：建立问题、标准来源和标准答案数据集。

## 22. 开工前需要确认的业务参数

以下是可配置项，不应阻塞开发，但上线前需要确认：

- 知识库是单租户还是多租户。
- 是否存在公开访问、登录或企业 SSO。
- 单文件和总知识库容量限制。
- 使用的 Embedding、Chat 模型及对应价格。
- 是否需要中文分词、OCR 或全文检索。
- 数据保存周期、删除策略和合规要求。
- 首 Token 延迟、并发量及每日调用预算。
