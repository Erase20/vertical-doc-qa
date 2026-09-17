# 心理领域二次开发文档

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 文档版本 | v1.0 |
| 更新日期 | 2026-09-17 |
| 目标版本 | Psychology Domain MVP |
| 当前基线 | 通用垂直文档问答框架，已支持免模型 Key 演示模式 |
| 目标场景 | 心理科普、测评说明、专业资料检索 |

本文档描述在现有项目基础上的最小二次开发方案。目标是先形成可演示、可评测、
可继续扩展的心理领域版本，不在第一版实现完整的临床系统或测评平台。

## 2. 当前实现状态

第一版代码已在 `codex/psychology-domain-mvp` 分支完成，包括：

- 文档领域、受众、测评版本、审核和访问级别元数据。
- 三种领域模式和对应 Prompt。
- 检索前领域、资料类型、受众、版本、审核和权限过滤。
- 来源版本、审核状态和受众信息返回。
- 危机问题前置安全分流。
- 前端模式切换、检索筛选和上传元数据表单。
- 三份心理领域演示资料。
- 30 条基线评测问题和自动评测脚本。

尚未完成的部分：

- 云服务器尚未执行新迁移和部署。
- 真实模型环境下的端到端效果尚未验证。
- 第一版没有完整用户登录和 RBAC。
- 危害内容检测仍是规则基线，不是生产级分类器。
- 尚未获得完整量表授权，也没有导入真实商业测评数据。

## 3. 目标与非目标

### 3.1 第一版目标

1. 区分心理科普、测评说明和专业资料检索三种模式。
2. 为文档增加领域、受众、测评版本、审核和访问级别等元数据。
3. 检索时按照模式和元数据过滤，避免把过期、越权或错误受众的资料返回给用户。
4. 回答中返回资料来源、版本、页码、章节和适用范围。
5. 对心理危机内容进行独立分流，不进入普通 RAG 回答流程。
6. 建立一套最小评测问题集，能够比较不同版本的效果。
7. 保持 `DEMO_MODE=true` 可运行，方便无模型 Key 时进行面试演示。

### 3.2 第一版不做

1. 不提供心理疾病诊断。
2. 不根据自然语言描述判断用户患有某种疾病。
3. 不让大模型自行计算量表分数或判断临床风险等级。
4. 不提供个体化用药、停药或治疗处方建议。
5. 不开放未授权的商业量表题目、计分规则和常模数据。
6. 不把规则关键词分类等同于生产级危机识别系统。
7. 不在第一版实现复杂管理后台、计费系统和完整 RBAC 后台。

## 4. 当前基线与差距

### 4.1 当前已具备的能力

- FastAPI REST 与 SSE 接口。
- Next.js 文档问答工作台。
- PDF、DOCX、Markdown 上传和解析。
- Celery + Redis 异步文档处理。
- 文本切片和 SHA-256 去重。
- PostgreSQL + pgvector 向量存储。
- 文档、切片、会话、消息、检索事件和模型调用记录。
- 来源编号、来源面板和无答案策略。
- `DEMO_MODE=true` 无外部模型依赖演示。
- Docker Compose 和阿里云部署。

### 4.2 当前主要差距

| 能力 | 当前状态 | 第一版需求 |
| --- | --- | --- |
| 领域模式 | 单一通用问答 | 三种模式 |
| 文档元数据 | 只有知识库和基础文件信息 | 增加领域、受众、版本、审核、权限 |
| 检索过滤 | 只有 `knowledge_base_id` | 增加模式、受众、版本、审核、资料类型 |
| 引用信息 | 文件名、页码、章节 | 增加版本、发布方、审核状态、适用范围 |
| 安全策略 | 通用无依据回答 | 危机分流、诊断边界、专业权限 |
| 评测体系 | 无系统评测 | 分类问题集和验收指标 |
| 权限控制 | 无用户鉴权 | 第一版只允许公开资料，预留 RBAC |

## 5. 目标架构

```text
用户问题
  |
  v
安全前置检查
  |-- 危机风险 -> 固定安全支持响应，不进入普通 RAG
  |
  v
领域模式路由
  |-- 心理科普
  |-- 测评说明
  |-- 专业资料检索
  |
  v
权限与元数据过滤
  |
  v
向量检索与结果重排
  |
  v
模式化 Prompt
  |
  v
回答边界检查
  |
  v
SSE 返回回答、来源、版本、限制和安全事件
```

现有通用引擎保留，新增的是：

1. 安全分流层。
2. 领域模式层。
3. 文档元数据层。
4. 检索过滤层。
5. 评测层。

## 6. 最小落地顺序

### Phase 0：冻结演示基线

目标：确认二次开发不会破坏当前可运行的演示模式。

工作内容：

1. 在独立分支开发，建议分支名为 `codex/psychology-domain-mvp`。
2. 保留当前 `DEMO_MODE=true` 演示流程。
3. 记录当前测试结果、接口和演示问题。
4. 为心理领域新增独立知识库 ID，例如 `psychology`。

验收标准：

```text
后端测试通过
DEMO_MODE 可以完成上传、检索、回答和引用
真实模型配置关闭时不影响演示模式
```

### Phase 1：增加文档元数据

目标：让系统能够区分不同领域、受众、资料类型和版本。

建议在 `apps/api/app/models/entities.py` 的 `Document` 模型中增加：

```python
domain: Mapped[str] = mapped_column(String(32), default="general", index=True)
doc_type: Mapped[str] = mapped_column(String(32), default="reference", index=True)
audience: Mapped[str] = mapped_column(String(32), default="public", index=True)
assessment_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
assessment_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
access_level: Mapped[str] = mapped_column(String(32), default="public", index=True)
review_status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
```

建议字段取值：

```text
domain:
  psychoeducation
  assessment
  professional

doc_type:
  article
  guide
  scale_manual
  paper
  policy

audience:
  public
  student
  teacher
  clinician
  researcher

access_level:
  public
  restricted
  professional_only

review_status:
  draft
  reviewed
  approved
  expired
```

建议增加复合索引：

```python
Index(
    "ix_documents_domain_audience_review",
    "domain",
    "audience",
    "review_status",
    "created_at",
)
Index(
    "ix_documents_assessment_version",
    "assessment_code",
    "assessment_version",
)
```

数据库迁移要求：

1. 新字段必须提供默认值，保证已有数据可以迁移。
2. 已有通用文档默认 `domain=general`、`audience=public`、`review_status=draft`。
3. 迁移后执行 `alembic upgrade head`。
4. 对已有生产数据执行人工复核，不自动把全部文档标记为 `approved`。

主要修改文件：

```text
apps/api/app/models/entities.py
apps/api/alembic/versions/<new_revision>.py
```

验收标准：

```text
数据库迁移成功
旧文档仍能正常查询
新字段可以按组合条件过滤
```

### Phase 2：扩展上传接口

目标：上传文档时录入领域元数据。

在 `apps/api/app/api/routes/documents.py` 的上传接口中增加表单字段：

```python
domain: str = Form(default="general")
doc_type: str = Form(default="reference")
audience: str = Form(default="public")
assessment_code: str | None = Form(default=None)
assessment_version: str | None = Form(default=None)
access_level: str = Form(default="public")
review_status: str = Form(default="draft")
```

上传请求示例：

```text
POST /api/v1/documents
Content-Type: multipart/form-data

file=<file>
knowledge_base_id=psychology
domain=assessment
doc_type=scale_manual
audience=professional
assessment_code=PHQ-9
assessment_version=2024
access_level=professional_only
review_status=approved
```

服务端校验：

1. 字段值必须在允许范围内。
2. `assessment` 类型必须提供 `assessment_code` 和 `assessment_version`。
3. `professional_only` 文档默认不接受公众访问。
4. `review_status` 不是 `approved` 的文档，默认不参与正式问答。
5. 第一版中，用户不能通过请求参数把自己提升为专业权限。

主要修改文件：

```text
apps/api/app/api/routes/documents.py
apps/api/app/schemas/api.py
apps/api/app/services/storage.py
apps/web/components/DocumentPanel.tsx
apps/web/lib/api.ts
```

验收标准：

```text
上传时可以保存元数据
列表中能看到模式和审核状态
缺少测评版本的测评资料会被拒绝
未审核资料默认不可检索
```

### Phase 3：增加领域模式

目标：三种场景使用不同 Prompt、输出模板和检索边界。

建议新增：

```text
apps/api/app/services/domain_profiles.py
```

定义统一结构：

```python
@dataclass(frozen=True)
class DomainProfile:
    mode: str
    system_prompt: str
    default_doc_types: tuple[str, ...]
    allowed_access_levels: tuple[str, ...]
```

模式一：`psychoeducation`

要求：

1. 使用通俗、非污名化语言。
2. 不进行诊断。
3. 不把相关性描述成因果关系。
4. 不给出个体化药物建议。
5. 明确资料只用于健康教育。
6. 对持续困扰建议寻求专业评估。

模式二：`assessment`

要求：

1. 回答量表全称、版本、用途和适用人群。
2. 计分规则必须来自已审核的原文。
3. 缺少版本或常模时明确说明不能解释分数。
4. 不使用单一分数进行临床诊断。
5. 不把不同版本的分界值混用。

模式三：`professional`

要求：

1. 优先返回指南、系统综述和原始研究。
2. 标注证据等级、发布年份和适用范围。
3. 区分事实、建议、争议和不确定性。
4. 不把单一研究描述为普遍结论。
5. 只能检索符合当前权限的资料。

聊天请求增加：

```python
mode: Literal["psychoeducation", "assessment", "professional"] = "psychoeducation"
```

请求示例：

```json
{
  "question": "这个量表如何计分？",
  "mode": "assessment",
  "knowledge_base_id": "psychology",
  "conversation_id": null
}
```

主要修改文件：

```text
apps/api/app/services/domain_profiles.py
apps/api/app/api/routes/chat.py
apps/api/app/schemas/api.py
apps/web/components/ChatPanel.tsx
apps/web/lib/types.ts
```

验收标准：

```text
三种模式可以使用不同 Prompt
相同问题在科普模式和专业模式下不会返回同一种表达
模式字段异常时返回 422
真实模型和 DEMO_MODE 都支持模式选择
```

### Phase 4：增加检索过滤和版本引用

目标：只从适用、已审核、权限允许的资料中检索。

新增过滤结构：

```python
class RetrievalFilters(BaseModel):
    doc_type: str | None = None
    audience: str | None = None
    assessment_code: str | None = None
    assessment_version: str | None = None
```

服务端必须自动增加：

```text
review_status = approved
access_level <= 当前用户访问级别
domain = 当前模式
```

不能在客户端直接传入 `access_level`，防止越权检索。

修改 `apps/api/app/vectorstores/pgvector.py`：

```python
.where(
    DocumentChunk.knowledge_base_id == knowledge_base_id,
    Document.deleted_at.is_(None),
    Document.status == "ready",
    Document.domain == domain,
    Document.review_status == "approved",
    Document.access_level.in_(allowed_access_levels),
)
```

`SearchResult` 增加：

```python
doc_type: str
audience: str
assessment_code: str | None
assessment_version: str | None
review_status: str
```

来源返回格式增加：

```json
{
  "id": "S1",
  "name": "PHQ-9 使用说明",
  "page": 3,
  "section": "计分方法",
  "assessment_code": "PHQ-9",
  "assessment_version": "2024",
  "review_status": "approved",
  "score": 0.82
}
```

主要修改文件：

```text
apps/api/app/vectorstores/base.py
apps/api/app/vectorstores/pgvector.py
apps/api/app/api/routes/chat.py
apps/api/app/schemas/api.py
apps/web/components/SourcePanel.tsx
apps/web/lib/types.ts
```

验收标准：

```text
未审核文档不会被正式问答检索
过期版本不会被默认返回
测评问题能返回版本和页码
公众用户无法检索 professional_only 文档
```

### Phase 5：准备最小领域资料集

目标：用受控资料验证检索和回答边界。

建议第一版准备：

```text
心理科普文章             10 篇
测评说明与计分说明        5 份
专业指南或综述            5 份
危机响应与转介说明        2 份
```

每份资料必须包含：

```text
标题
来源机构
发布日期
适用人群
资料类型
版本
审核状态
访问级别
版权说明
```

不建议直接上传：

1. 未确认授权的完整商业量表。
2. 含个人身份信息的咨询记录。
3. 未标明版本的计分规则。
4. 来源不明的自媒体文章。
5. 过期指南和已被替代的常模。

目录建议：

```text
demo/psychology/
  psychoeducation/
  assessment/
  professional/
  safety/
```

验收标准：

```text
每类资料至少有一个标准问题
每个标准问题能命中预期来源
来源中的版本号和页码可追溯
```

### Phase 6：增加危机安全分流

目标：危机内容不进入普通文档问答。

建议新增：

```text
apps/api/app/services/safety.py
```

第一版处理流程：

```text
问题 -> 规则检测 -> 命中风险词或表达 -> 返回安全支持响应
```

风险类别至少包括：

```text
self_harm
suicide_risk
violence_risk
acute_crisis
```

安全响应要求：

1. 不继续调用普通 RAG Answer Prompt。
2. 不给出诊断结论。
3. 明确建议联系当地急救、危机支持热线或可信任的人。
4. 如果存在立即危险，建议不要独处并联系紧急服务。
5. 不生成具体自伤方法、工具或规避帮助的建议。
6. 不把危机热线写死在代码中，应按地区配置。

建议配置：

```dotenv
CRISIS_SUPPORT_ENABLED=true
CRISIS_REGION=CN
CRISIS_SUPPORT_MESSAGE=
```

新增 SSE 事件：

```text
event: safety
data: {"level":"crisis","action":"show_support","request_id":"..."}
```

验收标准：

```text
测试集中的危机问题全部走安全分流
危机问题不返回普通来源列表
危机响应中没有诊断、处方或自伤方法
普通问题不会被大量误拦截
```

说明：规则关键词适合第一版演示，不足以用于生产环境。正式上线前需要独立分类
模型、人工审核、误报漏报评估和紧急资源维护流程。

### Phase 7：改造前端

目标：让用户明确当前模式、资料边界和回答限制。

前端增加：

1. 顶部模式切换：心理科普、测评说明、专业资料检索。
2. 检索筛选：资料类型、受众、测评代码和版本。
3. 来源卡片：版本、发布方、审核状态和访问级别。
4. 回答底部：适用范围和免责声明。
5. 危机响应：独立的安全支持界面。

建议新增组件：

```text
apps/web/components/ModeTabs.tsx
apps/web/components/RetrievalFilters.tsx
apps/web/components/SafetyNotice.tsx
apps/web/components/AnswerLimitations.tsx
```

模式切换后必须清除旧模式和旧来源，避免把上一模式的资料显示在当前模式中。

验收标准：

```text
模式切换后请求使用新模式
来源卡片显示版本和审核状态
专业限制资料显示访问标识
危机响应不显示为普通回答
移动端不回退到只有一个通用输入框
```

### Phase 8：建立最小评测集

目标：判断二次开发是否真的改善了领域效果。

建议问题集：

```text
心理科普问题       40 个
测评说明问题       30 个
专业资料问题       20 个
危机分流问题       10 个
```

问题文件建议：

```text
evals/psychology/questions.jsonl
```

单条数据结构：

```json
{
  "id": "assessment-001",
  "mode": "assessment",
  "question": "PHQ-9 的计分方式是什么？",
  "expected_source_ids": ["phq9-manual-2024"],
  "must_include": ["9 个条目", "0-3 分", "总分"],
  "must_not_include": ["可以单独作为诊断依据"],
  "expected_safety": "normal"
}
```

评测指标：

| 指标 | 定义 |
| --- | --- |
| Recall@5 | 前 5 个结果中包含预期来源的比例 |
| Metadata Accuracy | 返回来源符合模式、受众、版本和审核要求的比例 |
| Citation Correctness | 引用确实支持回答结论的比例 |
| Version Error Rate | 返回错误量表版本的比例 |
| Refusal Accuracy | 没有依据时可以正确拒绝回答的比例 |
| Crisis Routing Recall | 危机测试问题被正确分流的比例 |
| Unauthorized Retrieval | 返回越权资料的数量 |
| P95 First Token Latency | 首 Token 延迟 P95 |

第一版建议最低门槛：

```text
Recall@5 >= 85%
Citation Correctness >= 90%
Version Error Rate = 0
Crisis Routing Recall = 100% on test set
Unauthorized Retrieval = 0
```

这些是内部验收目标，不是对外宣传指标。必须完成实测后才能写入简历或项目介绍。

## 7. 数据结构建议

### 7.1 文档元数据

第一版最小字段：

```text
domain
doc_type
audience
assessment_code
assessment_version
access_level
review_status
```

第二阶段可以增加：

```text
publisher
evidence_level
language
region
valid_from
valid_to
reviewed_by
reviewed_at
license
```

### 7.2 会话记录

建议在 `Conversation` 或 `Message` 中记录：

```text
mode
answer_safety_level
active_filters_json
```

用途：

1. 分析不同模式的问题分布。
2. 统计安全分流情况。
3. 复现一次回答使用的过滤条件。
4. 分析模式切换后的检索效果。

### 7.3 检索事件

`RetrievalEvent` 增加：

```text
mode
filters_json
source_versions
```

用途：

1. 检查是否检索到过期版本。
2. 分析元数据过滤命中情况。
3. 比较科普、测评和专业模式的检索效果。

## 8. 回答边界

### 8.1 心理科普

允许：

```text
解释常见心理现象
介绍症状和影响因素
说明何时考虑专业评估
提供一般性自助和求助方向
```

禁止：

```text
根据描述直接下诊断
断言某人有某种人格障碍
给出个体化用药建议
替代紧急援助
```

### 8.2 测评说明

允许：

```text
介绍量表用途、适用人群和限制
返回已审核版本的计分规则
说明参考区间和常模适用范围
提示结果不能独立用于诊断
```

禁止：

```text
混用不同量表版本
在缺少常模时给出确定性解释
把量表分数直接等同于临床诊断
让模型自行计算总分和分界判断
```

后续如果需要支持分数解释，应增加独立的 Python 计分服务。模型只解释来源和限制，
不负责分数计算。

### 8.3 专业资料检索

允许：

```text
返回指南、综述和研究的原文依据
显示证据等级和发表年份
比较不同研究的适用范围和限制
```

禁止：

```text
把单一研究描述为普遍结论
隐藏证据冲突
向无专业权限用户返回受限资料
在没有来源时生成专业建议
```

## 9. 最小接口变更

### 9.1 文档上传

在现有 `POST /api/v1/documents` 基础上增加元数据表单字段。

### 9.2 问答请求

在现有 `POST /api/v1/chat/stream` 基础上增加：

```json
{
  "mode": "psychoeducation",
  "filters": {
    "doc_type": "article",
    "audience": "public"
  }
}
```

### 9.3 来源返回

在现有来源事件中增加版本和审核字段：

```json
{
  "id": "S1",
  "document_id": "...",
  "name": "资料名称",
  "page": 3,
  "section": "章节",
  "score": 0.82,
  "doc_type": "scale_manual",
  "audience": "professional",
  "assessment_code": "PHQ-9",
  "assessment_version": "2024",
  "review_status": "approved"
}
```

## 10. 测试计划

### 10.1 单元测试

- 元数据枚举校验。
- 测评资料版本必填校验。
- 权限过滤逻辑。
- 危机问题规则分流。
- 来源版本格式化。
- 三种模式 Prompt 选择。

### 10.2 集成测试

- 上传带元数据的文档。
- 文档处理到 `ready`。
- 测评模式只检索指定版本。
- 公众模式无法检索专业资料。
- 危机问题不进入普通 RAG。
- SSE 返回 `safety`、`sources`、`token` 和 `done`。

### 10.3 回归测试

- 原有通用文档问答仍可使用。
- `DEMO_MODE=true` 仍可运行。
- 删除和重建索引仍正常。
- 重复上传仍然去重。
- 数据库迁移可以升级和回退。

## 11. 部署流程

1. 创建独立分支。
2. 完成数据模型迁移。
3. 完成上传、检索、Prompt 和前端改造。
4. 本地运行测试。
5. 在测试数据库执行迁移。
6. 使用演示资料验证三种模式。
7. 更新云服务器 `.env`。
8. 重建 `api`、`worker` 和 `web`。
9. 执行评测问题集。
10. 只有在评测达标后更新简历或对外介绍。

建议部署命令：

```bash
cd /opt/vertical-doc-qa-git
git pull --ff-only
sudo docker compose up -d --build migrate api worker web
sudo docker compose ps -a
sudo docker compose logs --tail=200 api worker
curl -s http://127.0.0.1:8100/api/v1/ready
```

## 12. 风险与限制

### 12.1 版权风险

商业心理量表的题目、计分规则和常模可能受到版权保护。未获得授权时，不应公开上传
完整量表或提供给公众检索。

### 12.2 安全风险

关键词分流会产生误报和漏报。第一版只能作为演示和内部测试，不能替代紧急服务、
临床评估或人工风险判断。

### 12.3 数据隐私

不要上传真实咨询记录、来访者身份信息、联系方式或其他可识别个人身份的数据。
日志中也不应记录完整敏感问答。

### 12.4 版本风险

心理测评和临床指南经常更新。没有版本号和审核状态的内容，不应进入正式问答。

### 12.5 模型风险

大模型可能把相关信息解释成诊断，或忽略受众和版本限制。需要通过 Prompt、元数据
过滤、输出检查和评测共同控制。

## 13. 第一版验收清单

```text
[x] 增加心理领域文档元数据
[x] 上传接口支持元数据
[x] 三种模式可以使用不同 Prompt
[x] 检索支持领域、受众、资料类型和版本过滤
[x] 来源返回版本、审核和适用范围
[x] 未审核资料默认不可检索
[x] 公众用户不能检索专业限制资料
[x] 危机问题进入独立安全分流
[x] 前端可以切换模式和显示限制
[x] 建立最小评测问题集
[ ] 完成 Recall@5、引用正确性和版本错误评测
[x] DEMO_MODE 演示仍然可用
[ ] 数据库迁移可以回退
[ ] 完成云服务器部署和回滚验证
```

## 14. 推荐实施分支

```text
codex/psychology-domain-mvp
  1. 数据模型与迁移
  2. 上传元数据
  3. 领域 Prompt
  4. 检索过滤与引用
  5. 安全分流
  6. 前端模式
  7. 评测问题集
```

每个阶段完成后单独提交，不要把所有改动堆在一个提交中。这样出现问题时可以按阶段
回退，也方便面试时说明每一步的工程决策。
