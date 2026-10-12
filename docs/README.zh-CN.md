# AdoptLab 使用与开发指南

**AdoptLab 帮助 MCP 工具维护者在发布接入材料前，验证开发者能否完成真实任务，并将失败转化为可复验的材料修订。** 维护者将任务契约、接入指南、工具描述、运行证据和修订版本连接起来，依据独立验收决定材料是否具备发布证据。

[English](../README.md) · [公开案例](https://adoptlab.lukewilliams.top/) · [架构](architecture.md) · [任务包](mcp-task-packages.md) · [贡献指南](../CONTRIBUTING.md)

## 选择使用入口

| 角色 | 入口与目标 |
|---|---|
| 工具维护者 | 本地 `/workspace`：任务、实验、诊断、材料修订、复验与发布检查 |
| 首次接入开发者 | 本地 `/workspace#developer`：环境检查、首次任务、独立验收和反馈 |
| 案例读者 | 公开网站：双语交互式案例、脱敏报告和历史实验 |

本地工作台执行真实 MCP 工具；公开站点展示保存的案例与证据。工作台默认中文，提供十四个模块的英文界面。

## 安装并完成首次任务

准备 Git 和 Python 3.11 或以上。内置记录任务使用本机 CPU，无需 Docker、模型密钥或模型费用。以下命令在仓库根目录执行。

### Windows PowerShell

```powershell
git clone https://github.com/Oscar-Williams/adoptlab.git
Set-Location adoptlab
py -3.11 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
$env:ADOPTLAB_RUNTIME = Join-Path (Get-Location) "runtime"
& .\.venv\Scripts\adoptlab.exe doctor --target builtin
& .\.venv\Scripts\adoptlab.exe first-task
& .\.venv\Scripts\adoptlab.exe serve
```

### Linux / macOS

```bash
git clone https://github.com/Oscar-Williams/adoptlab.git
cd adoptlab
python3 -m venv .venv
.venv/bin/python -m pip install -e .
export ADOPTLAB_RUNTIME="$PWD/runtime"
.venv/bin/adoptlab doctor --target builtin
.venv/bin/adoptlab first-task
.venv/bin/adoptlab serve
```

`python3` 须对应 Python 3.11+。已有 Conda 用户可使用独立环境安装。命令通过环境内可执行文件运行，省去终端激活步骤。

打开 `http://127.0.0.1:8766/workspace#developer`。首次任务返回运行 ID、`passed` 和独立核验结果，核验失败返回非零退出码。页面提供执行、重新核验和反馈入口。Ctrl+C 停止服务；指定端口使用 `adoptlab serve --port 8780`。

`ADOPTLAB_RUNTIME` 保存 SQLite 数据库、运行产物及证据，已列入 Git 忽略规则。迁移时先制作一致性数据库备份，再完整保留被引用的产物和验证依据。

## 完成维护者闭环

1. 选择任务，或在编辑器预检后登记契约；预检返回字段错误，保持无登记、无执行副作用。
2. 选择工具集匹配的材料，冻结模式、条件和重复次数。
3. 执行任务，检查调用轨迹、独立验收和失败位置。
4. 从运行提交反馈，保存带修改理由的不可变材料版本。
5. 显式发起同条件复验，将通过独立验收的新运行关联到反馈；关联时重新检查证据和产物。
6. 对选定材料与任务集进行发布检查，下载证据。v2 导出保留原检查决定，同时提供当前重新核验结果。

`protocol` 按参考步骤调用真实工具，用于证明执行及验收链路；`model` 评价接入材料对模型执行的指导效果。可信模型比较要求条件一致且实际响应模型身份明确。

## 扩展 Filesystem 任务

启动 Linux Docker 引擎，确保 `docker` 可从 PATH 调用。准备脚本下载固定上游提交、解析基础镜像摘要、构建并登记工具、任务和匹配材料。镜像构建需要网络，任务容器按已登记隔离约束运行。

```powershell
# 使用当前环境内的 python 与 adoptlab。
& .\.venv\Scripts\python.exe scripts/prepare_filesystem.py --profile-id filesystem-v04 --task-id docs-evidence-v04 --image-tag adoptlab-filesystem:v04
& .\.venv\Scripts\adoptlab.exe doctor --target filesystem
& .\.venv\Scripts\adoptlab.exe run --config "$env:ADOPTLAB_RUNTIME/filesystem-run.json"
```

Linux/macOS 将最后一项参数改为 `"$ADOPTLAB_RUNTIME/filesystem-run.json"`。重新构建可能改变镜像摘要，应使用新工具配置与任务 ID 登记新版本。页面环境检查以所选配置为对象；详见[任务包与恢复规则](mcp-task-packages.md)。

## 开展模型实验

按 [.env.example](../.env.example) 配置被忽略的仓库 `.env`，或运行目录同级 `private/.env`。密钥仅保留在本地。当前执行器支持 `deepseek-flash`；执行前核对[官方价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)、冻结实验价格、剩余共享预算及未结算费用。

```powershell
& .\.venv\Scripts\adoptlab.exe doctor --target model
& .\.venv\Scripts\adoptlab.exe run --config examples/probe.json
& .\.venv\Scripts\adoptlab.exe compare --experiment "EXPERIMENT_ID_FROM_OUTPUT"
& .\.venv\Scripts\adoptlab.exe verify --run "RUN_ID_FROM_OUTPUT"
```

将引号内占位字符串替换为返回 ID。`probe.json` 发起付费模型请求，应先阅读其配置。默认最多八次模型请求（包含重试），每次最多 1,024 输出 token，截止时间 180 秒；实际约束由保存的实验配置决定。账本预留保守费用，未知请求结果保留预留状态，费用上界与供应商账单分别记录。

历史矩阵脚本用于复现较大规模付费实验。选择复现范围前阅读[实验结果与分母](experiment-results.md)。

## 理解项目证据

| 证据 | 内容 |
|---|---|
| [当前验证](../public-site/v05-validation.md) | 三案例与证据完整性行为 |
| [公开案例](https://adoptlab.lukewilliams.top/) | 内置记录、Filesystem 文档证据、配置字段及引用位置提取 |
| [历史实验](https://adoptlab.lukewilliams.top/experiments.html) | 独立保存原始矩阵；v0.2 包含 48 次协议检查和 144 轮模型实验 |
| [证据索引](evidence-index.md) | 设计决策、来源、版本及验证关系 |
| [试用准备](trial-and-resume.zh-CN.md) | 真实观察方法与参与后取证要求 |

协议验收、模型效果、自动化检查和真人观察分别统计。材料修订链路依据协议证据描述，模型改善依据受控模型实验描述，真实采用依据观察记录描述。

## 开发与检查

Windows 使用首次安装的环境执行：

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts/check_public_tree.py
& .\.venv\Scripts\python.exe scripts/build_static_site.py
```

Linux/macOS 使用 `.venv/bin/python`。测试使用隔离数据库并模拟付费调用。CI 分别运行 Windows、Linux 测试与 Filesystem 容器验收。[设计原则](../DESIGN.md)、[贡献指南](../CONTRIBUTING.md)和 [AGENTS.md](../AGENTS.md)约定后续修改与检查。

静态构建将白名单源文件写入 `dist/`，无需密钥或本地数据库。[发布说明](deployment.md)规定预览、检查和正式域名验证。本地执行服务绑定回环地址。

## 文件职责

| 目录 | 用途 |
|---|---|
| `adoptlab/` | 产品后端、模板、前端、执行器、数据库和独立验收 |
| `examples/` | 合成输入、任务契约与实验配置 |
| `tests/` | 契约、预算、状态、迁移与证据回归 |
| `scripts/` | 可复现集成、分析、正式材料生成和站点构建 |
| `docs/` | 使用、架构及带版本的验证证据 |
| `competitive/` | 可选 Promptfoo、Langfuse 集成 |
| `public-site/` | 双语证据站点及精选设计 |

本机工具路径记录在工作区 README；完整 Word、私人运行数据和临时检查文件保留在公开仓库之外。可选 Langfuse 适配器安装 `".[competitive]"`，使用自己的项目密钥和脱敏合成轨迹。[安全说明](../SECURITY.md) · [来源与许可](../NOTICE.md) · [更新记录](../CHANGELOG.md)。
