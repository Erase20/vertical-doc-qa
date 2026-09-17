# 面试演示运行指南

## 演示模式

项目的 `DEMO_MODE=true` 不依赖外部大模型 API Key。它可以完整运行以下链路：

```text
上传文档 -> 异步解析 -> 文本切片 -> 本地向量生成 -> pgvector 检索
-> SSE 流式回答 -> 来源引用 -> 调用记录
```

演示模式使用确定性本地向量和抽取式回答，不会调用真实大模型。面试时应当明确
说明这一点，避免把演示结果描述成真实 LLM 生成结果。

## 云服务器启动

进入部署目录并修改 `.env`：

```bash
cd /opt/vertical-doc-qa-git
nano .env
```

增加：

```dotenv
DEMO_MODE=true
```

重新构建 API 和 Worker：

```bash
sudo docker compose up -d --build api worker
sudo docker compose ps -a
sudo docker compose logs --tail=100 api worker
```

检查就绪状态：

```bash
curl -s http://127.0.0.1:8100/api/v1/ready
```

期望结果包含：

```json
{
  "status": "ready",
  "database": "ok",
  "redis": "ok",
  "model_configured": true,
  "model_mode": "demo"
}
```

## 现场演示流程

1. 打开 Web 页面。
2. 上传仓库中的 `demo/interview-sample.md`。
3. 等待文档状态从 `uploaded` 变为 `ready`。
4. 提问：`系统支持哪些文档格式？`
5. 展示流式回答、`[S1]` 引用和右侧来源面板。
6. 提问：`系统使用什么数据库存储向量？`
7. 提问一个文档中没有依据的问题，展示无答案策略。
8. 删除文档并重新上传，展示删除和 SHA-256 去重行为。

## 切换真实模型

面试结束后，如果要继续做效果评估，将服务器 `.env` 修改为：

```dotenv
DEMO_MODE=false
```

然后填写真实的 `LLM_*` 和 `EMBEDDING_*` 配置并重建。由于演示模式与真实模型
使用不同的向量空间，切换后需要删除并重新上传文档，或者对现有文档执行重建。
