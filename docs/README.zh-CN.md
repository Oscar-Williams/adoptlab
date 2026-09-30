# AdoptLab

比较界面按执行来源分别显示自动实验、本地浏览器与观察记录，支持自定义材料版本；验收摘要解释有效输出和正确拒绝。撤回后继续操作使用新匿名会话。

公开展示可使用 public-site 的保存结果浏览器：在本地具有冻结实验时运行 `python scripts/build_public_site.py`，导出独立白名单发布目录。页面不提供实时推理、上传或执行 API；当前完整工作台继续运行于本地。

[English](../README.md) · [架构与取舍](architecture.md) · [实测报告](experiment-results.md) · [竞品工作流](competitive.md)

**比较接入材料，验证首次任务，将反馈关联到经过验收的修订。** AdoptLab 面向维护文档、示例和工具描述的小型 API/MCP 团队。

首个任务读取合成记录，规范化整数金额与带时区日期，输出 JSON，再由独立实现的验证器检查。四个受限工具通过真实 stdio MCP 执行。维护者可创建不可变的接入指南与工具描述版本，保持后端和参数结构一致。

## 开始使用

在独立 Python 3.11 环境中，从项目目录执行：

```powershell
python -m pip install -e ".[dev,competitive]"
adoptlab doctor
adoptlab run --config examples/protocol.json
adoptlab serve
```

打开 `http://127.0.0.1:8766`，导航支持中英文切换。协议模式使用真实工具和确定性参考流程，不产生模型费用。

创建实验，分别执行 A/B；查看验收与独立复验；保存反馈，创建材料修订版本；用同一任务检查修订，再关联新旧结果并导出报告。页面代运行属于本地演示，独立开发者接入和受观察试用采用单独的证据口径。

## 真实模型与费用

将 `.env.example` 复制为被忽略的 `.env`，或将私有配置放在仓库外。设置 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL=deepseek-flash`，依据[官方价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)填写保守的人民币输入、输出单价（每百万 token）。实验 JSON 不包含密钥。

```powershell
adoptlab run --config examples/probe.json
adoptlab run --config examples/matrix.json
adoptlab compare --experiment <experiment-id>
adoptlab verify --run <run-id>
```

每 episode 最多八次模型请求，包含重试；每请求最多 1,024 输出 token，episode 超时 180 秒。SQLite 台账在请求前预留费用，网络结果不明时保留费用上界。报告采用保守单价，实际账单可能更低。首版模型接入限定为 DeepSeek Flash。

## 已测结果与适用范围

首个冻结矩阵包含十二个合成任务、两种材料、每任务三次 trial：A 通过 21/36，B 通过 36/36；正常产物和正确拒绝分开报告。24 次协议检查全部通过。[报告](experiment-results.md)记录任务族、失败、费用、相关重复与小样本限制。真实开发者采用和市场需求继续通过访谈、独立试用验证。

[Promptfoo、Langfuse 适配](../competitive/)复用同一执行器和验收规则。可选 tracing 仅记录合成实验的模型调用与工具步骤，并在发送前脱敏；不采集编码代理聊天或私人研究材料。Langfuse 需要本人项目配置：

```powershell
python competitive/langfuse_experiment.py
python scripts/langfuse_audit.py
```

公开导出排除密钥、个人路径、浏览器标识和自由文本。详见[安全说明](../SECURITY.md)。

## 实现与来源

材料版本、任务契约、验证器、预算、产品流程由 AdoptLab 新增实现。MCPMark 固定代码通过独立适配器完成上游状态隔离和原任务验收兼容性基线。[架构](architecture.md)、[来源锁](../upstream.lock.json)、[通知](../NOTICE.md)记录边界。

Windows、Python 3.11、现有 Edge、真实 stdio MCP、DeepSeek 和 Langfuse SDK 已本地验证。托管多人执行、任意外部工具、多模型兼容与真人试用结果按后续证据扩展。

AdoptLab 原创代码使用 MIT，外部项目保留各自许可。参见 [LICENSE](../LICENSE)、[贡献指南](../CONTRIBUTING.md)、[更新记录](../CHANGELOG.md)。
