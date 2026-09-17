# 面试演示运行指南

## 演示模式

项目的 `DEMO_MODE=true` 不依赖外部大模型 API Key。它可以完整运行以下链路：

```text
上传文档 -> 异步解析 -> 文本切片 -> 本地向量生成 -> pgvector 检索
-> 领域与权限过滤 -> SSE 流式回答 -> 来源引用 -> 调用记录
```

演示模式使用确定性本地向量和抽取式回答，不会调用真实大模型。面试时应当明确
说明这一点，避免把演示结果描述成真实 LLM 生成结果。

演示模式会自动使用 `professional_only` 访问级别，便于同一环境展示公开科普、
测评说明和专业受限资料。真实模式下访问范围由服务端 `ACCESS_LEVEL_CLEARANCE`
控制，客户端不能自行提升权限。

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

## 上传演示资料

依次上传以下文件，并使用表格中的元数据：

| 文件 | 资料领域 | 资料类型 | 适用人群 | 访问级别 | 测评代码 | 版本 |
| --- | --- | --- | --- | --- | --- | --- |
| `demo/psychology/psychoeducation/anxiety-basics.md` | 心理科普 | 科普文章 | 公众 | 公开 | 留空 | 留空 |
| `demo/psychology/assessment/demo-scale-guide.md` | 测评说明 | 测评手册 | 专业人员 | 仅专业人员 | `DEMO-9` | `2026` |
| `demo/psychology/professional/evidence-brief.md` | 专业资料 | 研究论文 | 研究人员 | 仅专业人员 | 留空 | 留空 |

审核状态统一选择“已审核”，等待文档状态从 `uploaded` 变为 `ready`。

## 现场演示流程

1. 打开 Web 页面。
2. 上传三份资料并等待处理完成。
3. 选择“心理科普”，提问：`焦虑通常有哪些表现？`
4. 展示流式回答、`[S1]` 引用和右侧来源元数据。
5. 选择“测评说明”，填写代码 `DEMO-9`、版本 `2026`，提问：
   `DEMO-9 如何计分？`
6. 选择“专业资料”，提问：`推广干预结论时有什么适用边界？`
7. 提问一个文档中没有依据的问题，展示无答案策略。
8. 在心理科普模式提问：`我不想活了，应该怎么办？`
9. 展示 `safety` 事件和危机支持响应，确认没有返回普通来源。
10. 删除文档并重新上传，展示删除和 SHA-256 去重行为。

## 切换真实模型

面试结束后，如果要继续做效果评估，将服务器 `.env` 修改为：

```dotenv
DEMO_MODE=false
```

然后填写真实的 `LLM_*` 和 `EMBEDDING_*` 配置并重建。由于演示模式与真实模型
使用不同的向量空间，切换后需要删除并重新上传文档，或者对现有文档执行重建。

真实模式下还必须由服务端设置访问范围：

```dotenv
ACCESS_LEVEL_CLEARANCE=public
```

当前第一版没有完整用户登录和 RBAC。不要把 `ACCESS_LEVEL_CLEARANCE` 暴露给
浏览器或允许客户端修改。
