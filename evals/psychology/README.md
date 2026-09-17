# 心理领域最小评测集

`questions.jsonl` 用于验证心理科普、测评说明、专业资料检索和危机分流四项能力。

## 当前样本

```text
心理科普      8
测评说明      8
专业资料      8
危机分流      6
合计         30
```

这是第一版最小基线。正式评估建议扩展到至少 100 个问题，并增加人工标注。

## 字段

```text
id                唯一编号
mode              请求使用的领域模式
question          测试问题
expected_sources  预期命中的来源文件
must_include      回答中必须出现或表达的内容
must_not_include  回答中不得出现的内容
expected_safety   预期安全级别：normal 或 crisis
```

## 评测指标

```text
Recall@5
Metadata Accuracy
Citation Correctness
Version Error Rate
Refusal Accuracy
Crisis Routing Recall
Unauthorized Retrieval
```

这些是内部验收指标。未完成真实语料和人工标注前，不应将结果写成对外宣传指标。

## 运行方式

```bash
python evals/psychology/run_eval.py \
  --base-url http://127.0.0.1:8100/api/v1
```

脚本会调用真实运行中的 `/chat/stream` 接口，并输出：

```text
Source hit
Safety routing
Citation present
Must-include coverage
```

`Must-include coverage` 使用字符串包含进行基线检查，不能替代人工语义评估。
