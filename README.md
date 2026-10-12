# AdoptLab

**Validate MCP onboarding materials against real developer tasks, then turn failures into verifiable material revisions.** AdoptLab is a local workspace for MCP tool maintainers who publish guides, examples and tool descriptions.

[中文](docs/README.zh-CN.md) · [Browse cases](https://adoptlab.lukewilliams.top/) · [Architecture](docs/architecture.md) · [Task contracts](docs/mcp-task-packages.md) · [Contributing](CONTRIBUTING.md)

## What you can do

Register independently accepted task contracts, run bounded MCP tasks, inspect traces and failures, revise immutable materials, explicitly retest under matching conditions, and export release evidence. Chinese is the default interface; English covers all fourteen modules.

The local application executes real tools. The public site provides interactive case walkthroughs and saved reports. Follow **task → material → run → diagnosis → revision → retest → release evidence**.

## Quick start: one verified task

Requirements: Git and Python 3.11 or newer. The built-in records task needs no Docker, model credentials or model fees. Run commands from the repository root.

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

Use a Python 3.11+ interpreter for `python3`. Existing Conda users can install into a dedicated environment instead of creating `.venv`.

Open [the developer entry](http://127.0.0.1:8766/workspace#developer). `first-task` returns a run ID, `passed` and an independent verification report; a failed check exits nonzero. The page provides checks, execution, re-verification and feedback. Stop the server with Ctrl+C. For another port use `adoptlab serve --port 8780` with your environment's executable.

`ADOPTLAB_RUNTIME` stores the SQLite database and run artifacts and is excluded from Git. Keep it writable. Before migration, take a consistent database backup and preserve referenced artifacts together with their evidence.

## Maintainer workflow

1. Select a task, or preflight and register a new contract. Preflight reports field errors without registration or execution.
2. Choose material whose tool descriptions match the task tools. Freeze mode, conditions and repetitions in an experiment.
3. Execute and inspect the tool trace and independent acceptance. Re-verify artifacts when investigating failures.
4. Save linked feedback and an immutable material version with a change reason.
5. Explicitly run the revision under the same conditions, then link the accepted run. Linking rechecks evidence and artifacts.
6. Check the selected material/task set and download evidence. The v2 release export preserves the original decision and adds current verification.

Protocol mode follows reference steps and proves execution/acceptance. Model mode evaluates material guidance for a bounded model executor. Model comparisons require matching conditions and known actual responders. [Current validation](public-site/v05-validation.md) covers records, Filesystem evidence and document configuration extraction.

## Optional Filesystem tasks

Start Docker with a Linux engine and put `docker` on PATH. Preparation downloads pinned upstream source, resolves base-image digests, builds the server and registers a profile, task and matching material. Building needs network access; task containers use configured isolation restrictions.

```powershell
# Use your active environment's Python and adoptlab executables.
& .\.venv\Scripts\python.exe scripts/prepare_filesystem.py --profile-id filesystem-v04 --task-id docs-evidence-v04 --image-tag adoptlab-filesystem:v04
& .\.venv\Scripts\adoptlab.exe doctor --target filesystem
& .\.venv\Scripts\adoptlab.exe run --config "$env:ADOPTLAB_RUNTIME/filesystem-run.json"
```

On Linux/macOS use `"$ADOPTLAB_RUNTIME/filesystem-run.json"` for the last argument. Rebuilding may change the digest: choose new profile/task IDs for a new build. The environment page checks the selected profile. See [contracts and recovery](docs/mcp-task-packages.md).

## Optional model experiments

Use [.env.example](.env.example) to configure an ignored repository `.env`, or `ADOPTLAB_RUNTIME/../private/.env`. Credentials stay out of experiment JSON, reports and screenshots. The current executor supports `deepseek-flash`; [check provider pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/) and frozen experiment prices before running.

Review `examples/probe.json`, remaining shared budget and unresolved reservations before launching this paid probe:

```powershell
& .\.venv\Scripts\adoptlab.exe doctor --target model
& .\.venv\Scripts\adoptlab.exe run --config examples/probe.json
& .\.venv\Scripts\adoptlab.exe compare --experiment "EXPERIMENT_ID_FROM_OUTPUT"
& .\.venv\Scripts\adoptlab.exe verify --run "RUN_ID_FROM_OUTPUT"
```

Replace quoted ID strings with returned IDs. Defaults allow eight model requests including retries, 1,024 output tokens per request and a 180-second deadline; saved settings control actual bounds. The SQLite ledger reserves conservative costs before requests and retains reservations for unknown outcomes. Cost upper bounds and provider billing are separate values.

Historical matrix scripts support reproducibility and launch larger paid experiments. Review [measured results and denominators](docs/experiment-results.md) before choosing a reproduction plan.

## Evidence and integrations

| Evidence | Scope |
|---|---|
| [Three-case walkthrough](https://adoptlab.lukewilliams.top/) | Saved protocol runs, revision links and downloadable reports |
| [Historical explorer](https://adoptlab.lukewilliams.top/experiments.html) | Original reports, including 48 protocol checks and 144 model episodes in v0.2 |
| [Evidence index](docs/evidence-index.md) | Decisions, provenance and version-specific validation |
| [Trial preparation](docs/trial-and-resume.zh-CN.md) | Observation method; adoption outcomes await recorded participation |

Protocol acceptance, model outcomes, automated checks and human observations use separate populations and denominators. Revised protocol cases establish the workflow; material effectiveness requires controlled model evidence and adoption requires observations.

[Promptfoo and Langfuse adapters](docs/competitive.md) reuse the bounded executor and verifier. Install `".[competitive]"` for the optional Langfuse adapter. Tracing uses your own project credentials and masked synthetic generations/tool calls.

## Develop and check

Use the environment created above. Windows PowerShell:

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m pytest -q
& .\.venv\Scripts\python.exe scripts/check_public_tree.py
& .\.venv\Scripts\python.exe scripts/build_static_site.py
```

On Linux/macOS use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe`. Tests isolate databases and paid calls. CI checks Windows and Linux, with separate Filesystem integration. [Design principles](DESIGN.md), [contributor instructions](CONTRIBUTING.md) and [agent guidance](AGENTS.md) define change expectations.

The static build reads allowlisted source assets into `dist/` without credentials or runtime data. [Deployment](docs/deployment.md) describes Pages previews and production checks. Keep execution bound to loopback; the public site serves saved evidence.

## Repository map

| Path | Purpose |
|---|---|
| `adoptlab/` | FastAPI, Jinja2, JS/CSS, SQLite, MCP execution and verification |
| `examples/` | Synthetic fixtures, contracts and bounded configurations |
| `tests/` | Contract, budget, state, migration and evidence regressions |
| `scripts/` | Reproducible integration, analysis, material and site generation |
| `docs/` | Setup, architecture and version-labeled evidence |
| `competitive/` | Optional evaluation adapters |
| `public-site/` | Bilingual saved-evidence site and selected editable designs |
| `upstream.lock.json`, `NOTICE.md` | Pinned provenance and external licenses |

Private runtime data, full local Word deliverables, workspace-specific paths and temporary QA files stay outside the public tree. [Security](SECURITY.md) defines data handling and disclosure. Original code is MIT licensed; external projects retain their licenses. [License](LICENSE) · [Changelog](CHANGELOG.md).
