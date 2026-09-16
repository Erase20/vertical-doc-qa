# 垂直文档问答助手开发记录

> 记录日期：2026-09-16  
> 当前阶段：初始框架已部署，模型接口配置和完整业务验证尚未完成  
> 代码仓库：`git@github.com:Erase20/vertical-doc-qa.git`

## 1. 文档目的

本文记录项目从需求整理、代码搭建、本地验证、Git 管理到阿里云部署的完整过程，并明确当前完成状态、关键配置、遇到的问题和下一步工作。

本文不记录任何真实 API Key、数据库密码或 GitHub 私钥。

## 2. 项目目标

项目是一个面向垂直领域资料的文档问答助手，计划支持：

- 上传 PDF、Word 和 Markdown。
- 解析文档并按段落切片。
- 调用 Embedding 接口生成向量。
- 使用 PostgreSQL 和 pgvector 保存和检索向量。
- 检索最相关的 5 个片段。
- 调用大模型生成带来源的回答。
- 使用 SSE 流式返回回答。
- 记录调用耗时、Token 和成本。
- 提供上传、聊天和来源展示页面。
- 使用 Docker Compose 启动全部服务。

## 3. 技术架构

```text
浏览器
  -> Next.js 前端
  -> FastAPI API
  -> PostgreSQL + pgvector
  -> Redis
  -> Celery Worker
  -> Embedding API
  -> LLM API
```

主要技术：

| 模块 | 技术 |
| --- | --- |
| 前端 | Next.js 14、React 18、TypeScript、原生 CSS |
| 后端 | Python、FastAPI、Pydantic、SQLAlchemy |
| 数据库 | PostgreSQL 16、pgvector |
| 异步任务 | Celery、Redis |
| 文档解析 | PyMuPDF、python-docx |
| 模型接口 | OpenAI Compatible API |
| 数据库迁移 | Alembic |
| 部署 | Docker、Docker Compose |
| 代码管理 | Git、GitHub |

## 4. 已完成的开发工作

### 4.1 开发文档

已编写 [DEVELOPMENT_DOSSIER.md](D:/Project/test/DEVELOPMENT_DOSSIER.md)，内容包括：

- 项目范围和技术方案。
- 文档解析与段落切片规则。
- Embedding 和 pgvector 设计。
- Top 5 检索和来源引用。
- SSE 流式协议。
- API 和数据模型。
- Token 与成本计算。
- 前端页面要求。
- Docker 部署方案。
- 测试、安全和后续演进。

### 4.2 后端

已实现 FastAPI 应用和以下接口：

```text
GET    /api/v1/health
GET    /api/v1/ready
POST   /api/v1/documents
GET    /api/v1/documents
GET    /api/v1/documents/{id}
DELETE /api/v1/documents/{id}
POST   /api/v1/documents/{id}/reindex
POST   /api/v1/chat/stream
GET    /api/v1/metrics/calls
```

后端已经包含：

- PDF、DOCX、Markdown 解析。
- 按段落合并和切片。
- 文档状态机。
- Celery 异步处理任务。
- Embedding 接口封装。
- LLM 流式接口封装。
- pgvector 余弦距离检索。
- SSE 回答协议。
- 会话、消息、检索记录和调用记录模型。
- 文件大小、扩展名和内容哈希校验。
- 数据库初始化迁移。

### 4.3 前端

已实现 Next.js 工作台页面：

- 左侧上传和文档列表。
- 中间聊天和流式回答。
- 右侧检索来源。
- 文档处理状态轮询。
- `[S1]` 等引用定位。
- 上传、删除和重建索引操作。

主要前端文件：

```text
apps/web/app/page.tsx
apps/web/components/DocumentPanel.tsx
apps/web/components/ChatPanel.tsx
apps/web/components/SourcePanel.tsx
apps/web/lib/api.ts
```

### 4.4 Docker

已创建 Docker Compose 服务：

```text
postgres
redis
migrate
api
worker
web
```

已完成的构建优化：

- 前端和后端使用多阶段或轻量基础镜像。
- Worker 默认并发数改为 1。
- Embedding 批大小改为可配置，默认 25。
- 移除不必要的 Debian apt 安装。
- 支持配置 pip 和 npm 国内镜像。
- 数据库和上传文件使用 Docker Volume 持久化。

## 5. 本地验证结果

已经完成的验证：

```text
后端测试：2 passed
Ruff：通过
TypeScript 类型检查：通过
Next.js lint：通过
Next.js 生产构建：通过
Alembic 离线 SQL：通过
Docker Compose YAML：解析通过
```

本地 Python 解释器：

```text
D:\Project\test\apps\api\.venv\Scripts\python.exe
Python 3.10.11
```

Docker 容器内 Python 版本：

```text
Python 3.12
```

## 6. Git 和 GitHub

本地已经初始化 Git 仓库，并推送到 GitHub。

当前提交：

```text
684d84b Make embedding batch size configurable
1d259db Initial vertical document QA framework
```

远程地址：

```text
git@github.com:Erase20/vertical-doc-qa.git
```

Git 已忽略：

```text
.env
.venv
venv
node_modules
.next
.idea
*.tar.gz
本地测试上传文件
```

服务器使用 GitHub Deploy Key，并通过以下 SSH 配置访问：

```text
Host github-docqa
    HostName ssh.github.com
    User git
    Port 443
    IdentityFile ~/.ssh/github_docqa
    IdentitiesOnly yes
```

## 7. 阿里云服务器部署记录

服务器信息：

```text
系统：Alibaba Cloud Linux 3
架构：x86_64
内存：约 1.8 GB
磁盘：40 GB
公网 IP：182.92.182.246
```

因为内存较小，已经增加 4 GB Swap，并设置：

```text
vm.swappiness=10
```

已经完成：

- 使用阿里云 Docker CE 软件源安装 Docker。
- 安装 Docker Compose Plugin。
- 验证 `hello-world` 容器。
- 在服务器生成 GitHub Deploy Key。
- 通过 SSH over 443 连接 GitHub。
- 将仓库克隆到 `/opt/vertical-doc-qa-git`。
- 创建服务器 `.env`。
- 构建 API、Worker 和 Web 镜像。
- 启动 PostgreSQL 和 Redis。
- 执行 Alembic 初始迁移。
- 启动 API、Worker 和 Web。
- 前端页面已经可以打开。

当前 Windows 源代码目录：

```text
D:\Project\test
```

当前服务器 Git 部署目录：

```text
/opt/vertical-doc-qa-git
```

旧解压目录暂时保留：

```text
/opt/vertical-doc-qa
```

后续应只从 `/opt/vertical-doc-qa-git` 更新和启动项目。

## 8. 当前服务器端口

| 用途 | 服务器端口 | 容器端口 |
| --- | --- | --- |
| Web | 3100 | 3000 |
| API | 8100 | 8000 |
| PostgreSQL | 不对外开放 | 5432 |
| Redis | 不对外开放 | 6379 |

阿里云安全组需要开放：

```text
22
3100
8100
```

不应开放：

```text
5432
6379
```

当前访问地址：

```text
Web: http://182.92.182.246:3100
API 文档: http://182.92.182.246:8100/docs
就绪检查: http://182.92.182.246:8100/api/v1/ready
```

## 9. 当前运行状态

已验证：

```text
PostgreSQL：healthy
Redis：healthy
Alembic migrate：Exited (0)
Worker：已连接 Redis，celery ready
Web：页面可以打开
```

尚未完成：

```text
LLM_API_KEY：为空
EMBEDDING_API_KEY：为空
model_configured：当前为 false
文档上传后的 Embedding：未验证
真实问答和来源返回：未验证
```

因此当前页面可以打开，但文档处理会因模型未配置而失败，聊天也不能生成真实回答。

## 10. 推荐模型配置

当前更适合使用阿里云百炼 OpenAI 兼容接口。

推荐配置：

```dotenv
LLM_BASE_URL=百炼控制台提供的兼容接口地址
LLM_API_KEY=百炼 API Key
LLM_MODEL=qwen-plus

EMBEDDING_BASE_URL=百炼控制台提供的兼容接口地址
EMBEDDING_API_KEY=百炼 API Key
EMBEDDING_MODEL=text-embedding-v2
EMBEDDING_DIMENSION=1536
EMBEDDING_BATCH_SIZE=25
```

选择 `text-embedding-v2` 的原因：

- 输出维度为 1536。
- 与数据库中的 `VECTOR(1536)` 一致。
- 当前不需要修改数据库向量列。

Base URL 必须使用百炼控制台实际提供的地址，不要自行拼接或使用过期示例。

## 11. 遇到的主要问题

### 11.1 本机没有 Docker

最初尝试在 Windows 本机使用 Docker，但 WSL2 下载较慢。

解决方式：

- 改用阿里云服务器运行 Docker。
- 保留本地 Windows 环境用于开发和 Git 提交。

### 11.2 Docker 构建卡住

主要原因是默认 Docker、apt、pip 或 npm 下载较慢。

解决方式：

- 移除不需要的 apt 安装。
- 使用国内 pip 和 npm 镜像。
- 串行构建，限制并行度。
- 增加 4 GB Swap。

### 11.3 GitHub HTTPS 无法连接

本地访问 `github.com:443` 超时，但 SSH 正常。

解决方式：

- 将 Git 远程地址改为 SSH。
- 服务器使用 `ssh.github.com:443` 和 Deploy Key。

### 11.4 `.env` 粘贴后出现格式问题

聊天或 Markdown 渲染可能影响包含下划线和 URL 的文本。

解决方式：

- 使用原始字节检查配置。
- 必要时使用 Base64 写入 `.env`。
- 不通过聊天传递真实密钥。

## 12. 日常开发流程

本地修改：

```powershell
cd D:\Project\test
git add .
git commit -m "描述本次修改"
git push
```

服务器更新：

```bash
cd /opt/vertical-doc-qa-git
git pull --ff-only
sudo docker compose up -d --build
```

只修改后端时：

```bash
sudo docker compose up -d --build api worker
```

只修改前端时：

```bash
sudo docker compose up -d --build web
```

查看状态和日志：

```bash
sudo docker compose ps -a
sudo docker compose logs --tail=200 api worker web
```

## 13. 数据安全

- `.env` 不提交 Git。
- PostgreSQL 和 Redis 不映射到公网。
- Docker Volume 保存数据库、Redis 和上传文件。
- `docker compose down` 不会删除 Volume。
- `docker compose down -v` 会删除 Volume，不能随意执行。
- 当前数据库密码 `docqa` 仅用于测试，正式使用前应更换。
- API 当前没有用户鉴权，正式公开前应增加访问控制。

## 14. 下一步任务

1. 在阿里云百炼创建 API Key。
2. 获取正确的 OpenAI 兼容 Base URL。
3. 在服务器 `.env` 中填写 LLM 和 Embedding 配置。
4. 重建并重启 `api` 和 `worker`。
5. 检查 `/api/v1/ready`，确认 `model_configured` 为 `true`。
6. 上传一份 Markdown 文档并确认状态变为 `ready`。
7. 测试一个可回答问题。
8. 测试一个文档中没有依据的问题。
9. 检查回答来源、耗时和 Token 记录。
10. 完成后再处理域名、HTTPS、鉴权和生产级安全加固。

## 15. 当前结论

项目初始框架已经完成并部署到阿里云服务器：

```text
代码已纳入 Git 和 GitHub
Docker 环境已可用
数据库迁移已成功
PostgreSQL、Redis、API、Worker、Web 已运行
前端页面已能访问
```

项目尚未形成完整可用的文档问答闭环，原因是 LLM 和 Embedding API Key 尚未配置。下一阶段的核心任务不是继续扩展功能，而是完成模型接口配置并进行端到端验证。
