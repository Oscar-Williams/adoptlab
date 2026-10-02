# Verify a first MCP task and revise its onboarding materials

This tutorial uses synthetic records and the local protocol workflow. It makes no model call and uploads no telemetry.

## Run a verified task

Create an independent Python 3.11 environment, install the package, and check it:

```powershell
python -m pip install -e .
$env:ADOPTLAB_RUNTIME = "F:\Dev\adoptlab-runtime"
adoptlab doctor --target builtin
adoptlab first-task
adoptlab serve
```

Choose your own writable data-drive directory instead of the example path. On Linux use `export ADOPTLAB_RUNTIME=/path/to/adoptlab-runtime`. Open `http://127.0.0.1:8766/?view=developer` for the four-step path: check environment, run one task, independently verify and submit linked feedback. The CLI stores exactly one protocol run and a verification summary. Docker, API credentials and Langfuse are optional for this task.

Open the maintainer workspace to create an experiment. Choose a material version and a task, then run it in protocol mode. This mode uses a deterministic reference workflow through the real MCP connection. The independent verifier checks money, dates, filtering and both output files.

Inspect the run status and verification reason. Use **Re-verify** to check the stored artifacts. A verified rejection is a valid result for intentionally invalid input; ordinary tasks need valid outputs.

**Compare material versions** shows each execution cohort separately. Automated trials, local browser sessions and observed human sessions retain their own denominators. A browser session establishes local execution, without establishing a unique participant. The verdict summary explains valid output and correct rejection alongside the raw evidence.

## Make a material revision

Submit feedback describing the obstacle. In the material editor, use B as a starting point, change the guide or one of the four descriptions, and save a new immutable version. Existing versions remain unchanged.

Run the same task using the new version and link the verified run to the feedback. Protocol mode validates the mechanism; use model mode after credentials and current prices are configured to study whether changed materials alter model behavior. Keep the backend, task and verifier fixed and retain failures.

Export the allowlisted report. It contains verdicts, provenance and cost upper bounds, with no private keys, personal paths or free-text feedback. Separate observed developer participation from model experiments and automated browser checks.

Withdrawing a browser's adoption records removes linked events/feedback and anonymizes its runs. Continuing creates a fresh anonymous session and clears previous run/feedback links. Private run artifacts and external telemetry have separate retention boundaries.

## Read results and choose the next step

The [v0.2 model experiment](experiment-results.md) separates guide and description changes across four combinations. The public explorer defaults to model runs and offers separate protocol, cohort and task-split filters. Its walkthrough compares saved runs with matching task, trial, execution fingerprints and known responder. The historical v0.1 report remains downloadable. Independent developer integration remains an external validation task.

If your team already uses [Promptfoo or Langfuse](competitive.md), evaluate whether an AdoptLab template or adapter fits the existing process. The standalone workspace adds an integrated feedback-to-revision path while keeping a deliberately small task catalog.

## Short demonstration script

1. Show the maintainer's question: did this onboarding change improve a defined first task?
2. Open an experiment and inspect one failure alongside a passing variant.
3. Explain the independent acceptance rule and the difference between valid output and correct input rejection.
4. Save a new material version, run the same task and associate the verified revision with feedback.
5. Export a report and show the limits: local operation, synthetic tasks, one model and pending human trials.

Use real saved results when recording. Label protocol demonstrations and automated runs. Request permission before recording participants or publishing their comments.

## External Filesystem task

See [MCP task packages](https://github.com/Oscar-Williams/adoptlab/blob/main/docs/mcp-task-packages.md) to build the pinned offline container and register its task. Container integration is optional for the built-in records quick start. Run adoptlab doctor to check Docker readiness. No model key is needed for python scripts/verify_filesystem.py --protocol-only.
