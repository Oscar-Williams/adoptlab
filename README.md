# AdoptLab

[中文](docs/README.zh-CN.md) · [Architecture](docs/architecture.md) · [Measured results](docs/experiment-results.md) · [Competitive workflow](docs/competitive.md)

**Compare onboarding materials, verify a developer task, and link feedback to a tested revision.** AdoptLab is a local workspace for small API/MCP teams maintaining their documentation, examples and tool descriptions.

The first task reads synthetic records, normalizes integer money and timezone-aware dates, writes JSON outputs and checks them with an independently implemented oracle. Four restricted tools run through a real stdio MCP connection. Maintainers can create immutable guide/description versions while preserving the backend and tool schemas.

## Try it

Use an independent Python 3.11 environment. From this directory:

```powershell
python -m pip install -e ".[dev,competitive]"
adoptlab doctor
adoptlab run --config examples/protocol.json
adoptlab serve
```

Open `http://127.0.0.1:8766`. English is the default; the navigation switches to Chinese. Protocol mode uses real tools with a deterministic reference workflow and incurs no model fee.

1. Create an experiment and run a task with A and B.
2. Inspect verification and use **Re-verify** to check artifacts again.
3. Save feedback, create a revised material version, and run the same task.
4. Link the new verified run to the feedback and export a report.

The browser executes a local demonstration. Independent developer integration and observed user trials have separate evidence requirements.

Material comparison includes separately labeled execution cohorts and custom versions. Verdict summaries distinguish valid output from correct rejection. Withdrawing records starts a fresh anonymous browser session for subsequent actions.

## Real model runs

Copy `.env.example` to an ignored `.env`, or use a private configuration outside the repository. Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL=deepseek-flash` and current conservative CNY input/output prices per million tokens. Check [DeepSeek pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) before running. Credentials are never placed in experiment JSON.

```powershell
adoptlab run --config examples/probe.json
adoptlab run --config examples/matrix.json
adoptlab compare --experiment <experiment-id>
adoptlab verify --run <run-id>
```

Each episode has eight model requests including retries, 1,024 output tokens per request and a 180-second deadline. A shared SQLite ledger reserves the worst-case request cost before sending. Unknown network outcomes keep their reservation. Reports use a conservative cost upper bound; provider invoice charges may be lower. The initial integration supports DeepSeek Flash only.

## What has been measured

The first frozen matrix contains twelve synthetic tasks, two material versions and three trials: A passed 21/36, B passed 36/36. Normal outputs and correct input rejection are reported separately. Protocol checks passed 24/24. [The report](docs/experiment-results.md) documents task families, failures, costs, correlated repeats and small-sample limits. It supports this material comparison under these conditions. Real developer adoption and market demand remain to be validated.

## Integrate with evaluation tools

[Promptfoo and Langfuse adapters](competitive/) use the same bounded executor and verifier. This keeps the task consistent while comparing configuration, assertions, reporting and feedback workflows. Optional Langfuse tracing records synthetic model generations and tool calls with pre-export masking; it does not capture coding-agent conversations or personal research files.

```powershell
python competitive/langfuse_experiment.py
python scripts/langfuse_audit.py
```

Cloud tracing requires your own Langfuse project credentials. Public exports omit keys, personal paths, browser identifiers and free text. See [Security](SECURITY.md).

## Scope and provenance

AdoptLab contains the original onboarding/version/verification/budget/product workflow and a narrow [MCPMark adapter](adoptlab/upstream.py). MCPMark's pinned checkout supplies upstream task setup and verification for an interoperability baseline; the custom records executor is original code. [Architecture decisions](docs/architecture.md) explain this separation and the tested Windows path. [Upstream lock](upstream.lock.json) and [notices](NOTICE.md) preserve sources and licenses.

Windows/Python 3.11, the installed Edge browser, real stdio MCP, DeepSeek and Langfuse SDK have been exercised locally. Hosted multi-user execution, arbitrary external tools, broad model compatibility and independent human trial outcomes are future work.

MIT for original AdoptLab code. External projects retain their own licenses. See [LICENSE](LICENSE), [Contributing](CONTRIBUTING.md) and [Changelog](CHANGELOG.md).

## Publication preview

The [static explorer](public-site/) browses allowlisted saved results without a backend, uploads or inference calls. With the frozen experiment available in your local runtime, `python scripts/build_public_site.py` generates a separate publication directory. This directory contains only the public assets and report, and is the unit to deploy. Keep the execution service local until authentication, isolation and resource governance have been implemented for remote use.
