# AdoptLab

[中文](docs/README.zh-CN.md) · [Architecture](docs/architecture.md) · [Measured results](docs/experiment-results.md) · [Competitive workflow](docs/competitive.md)

**Compare onboarding materials, verify a developer task, and link feedback to a tested revision.** AdoptLab is a local workspace for small MCP tool teams maintaining their documentation, examples and tool descriptions.

The first task reads synthetic records, normalizes integer money and timezone-aware dates, writes JSON outputs and checks them with an independently implemented oracle. Four restricted tools run through a real stdio MCP connection. Maintainers can create immutable guide/description versions while preserving the backend and tool schemas.

## v0.3 first-success workspace

Register pinned offline MCP containers, import immutable task contracts, inspect run history, compare material lineage and export a safe problem package. The official Filesystem example adds a second task contract beyond the built-in records workflow. [Task-package tutorial](docs/mcp-task-packages.md) · [v0.2 decisions](docs/v02-decisions.md) · [v0.2 validation](docs/v02-validation.md).

The developer entry follows environment check → one task → independent acceptance → linked feedback. `adoptlab first-task` runs one CPU protocol task and saves its verification report. [Product PRD](docs/product-prd.md) · [v0.3 validation](docs/v03-validation.md). The public site provides a saved-evidence walkthrough; local installation enables execution.

## Published evidence

[Open the bilingual explorer](https://adoptlab.lukewilliams.top) · [Pages mirror](https://adoptlab.pages.dev). Inspect the frozen v0.2 matrix: 48 protocol checks and 144 model episodes, with a historical 72-episode report, filter task families and download the reviewed report. The full execution workspace runs locally.

## Try it

Use an independent Python 3.11 environment. Clone this repository onto your data drive, create/activate a Conda or venv environment, then run from this directory. The runtime path below is an example; choose your own writable directory. On Linux set `export ADOPTLAB_RUNTIME=/path/to/adoptlab-runtime`. Optional development/competitor dependencies are installed with `python -m pip install -e ".[dev,competitive]"`.

```powershell
python -m venv F:\Dev\adoptlab-env
F:\Dev\adoptlab-env\Scripts\Activate.ps1
python -m pip install -e .
$env:ADOPTLAB_RUNTIME = "F:\Dev\adoptlab-runtime"
adoptlab doctor --target builtin
adoptlab first-task
adoptlab serve
```

Open `http://127.0.0.1:8766/?view=developer`. English is the default; the navigation switches to Chinese. Protocol mode uses real tools with a deterministic reference workflow and incurs no model fee.

Start with **Run first task** on the developer page. Re-verify its saved artifacts and submit feedback. Open the maintainer workspace for the full comparison/revision workflow:

1. Create an experiment and run a task with A and B.
2. Inspect verification and use **Re-verify** to check artifacts again.
3. Save feedback, create a revised material version, and run the same task.
4. Link the new verified run to the feedback and export a report.

The browser executes a local demonstration. Independent developer integration and observed user trials have separate evidence requirements.

Material comparison includes separately labeled execution cohorts and custom versions. Verdict summaries distinguish valid output from correct rejection. Withdrawing records starts a fresh anonymous browser session for subsequent actions.

## Real model runs

Copy `.env.example` to an ignored `.env`, or use a private configuration outside the repository. Set `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL=deepseek-flash` and verify the conservative CNY prices recorded in the experiment configuration. Local price environment variables are retained for compatibility; frozen experiment prices control reservation and costing. Check [DeepSeek pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) before running. Credentials are never placed in experiment JSON.

```powershell
adoptlab run --config examples/probe.json
adoptlab run --config examples/matrix.json
adoptlab compare --experiment <experiment-id>
adoptlab verify --run <run-id>
```

Default episode limits are eight model requests including retries, 1,024 output tokens per request, 8,192 output tokens total and a 180-second deadline. Experiment settings can reduce these bounds. Saved configuration controls actual execution. A shared SQLite ledger reserves the worst-case request cost before sending. Unknown network outcomes keep their reservation. Reports use a conservative cost upper bound; provider invoice charges may be lower. The initial integration supports DeepSeek Flash only.

## Run the new factorial

```powershell
python scripts/run_v02_matrix.py
python scripts/analyze_v02.py
```

This freezes a guide × tool-description factorial with 48 protocol checks and 144 model trials. It retains task-family holdouts, original failures and uncertain request reservations. It requires configured model credentials and uses the existing shared budget ledger.

## What has been measured

The v0.2 factorial contains 48 protocol checks (48 passed) and 144 model episodes: AA 23/36, AB 35/36, BA 36/36, BB 36/36. One pre-response failure retains an unknown responder and remains in the denominator. [Experiment results](docs/experiment-results.md) describe task-family holdouts, conservative costs and exploratory contrasts. [Historical v0.1 evidence](docs/experiment-results-v1.md) remains available. [Review and iteration](docs/review-results.md) separates Codex simulations from observed participants. Real developer adoption remains unmeasured.

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

The [static explorer](public-site/) browses allowlisted saved results without a backend, uploads or inference calls. `python scripts/build_static_site.py` builds the complete committed site into `dist` without local runtime data or third-party dependencies. [Cloudflare Pages Git integration](docs/deployment.md) automatically publishes this directory on updates. The local exporter `scripts/build_public_site.py` prepares evidence for review before updating committed assets. Keep the execution service local until authentication, isolation and resource governance have been implemented for remote use.

[Evidence index](docs/evidence-index.md) connects product decisions, original mechanisms, experiments, review changes and release checks.
