# Verify a first MCP task and revise its onboarding materials

This tutorial uses synthetic records and the local protocol workflow. It makes no model call and uploads no telemetry.

## Run a verified task

Create an independent Python 3.11 environment, install the package, and check it:

```powershell
python -m pip install -e .
adoptlab doctor
adoptlab run --config examples/protocol.json
adoptlab serve
```

Open the local address printed by the server. Create an experiment. Choose a material version and a task, then run it in protocol mode. This mode uses a deterministic reference workflow through the real MCP connection. The independent verifier checks money, dates, filtering and both output files.

Inspect the run status and verification reason. Use **Re-verify** to check the stored artifacts. A verified rejection is a valid result for intentionally invalid input; ordinary tasks need valid outputs.

## Make a material revision

Submit feedback describing the obstacle. In the material editor, use B as a starting point, change the guide or one of the four descriptions, and save a new immutable version. Existing versions remain unchanged.

Run the same task using the new version and link the verified run to the feedback. Protocol mode validates the mechanism; use model mode after credentials and current prices are configured to study whether changed materials alter model behavior. Keep the backend, task and verifier fixed and retain failures.

Export the allowlisted report. It contains verdicts, provenance and cost upper bounds, with no private keys, personal paths or free-text feedback. Separate observed developer participation from model experiments and automated browser checks.

## Read results and choose the next step

The [first model experiment](experiment-results.md) has 72 episodes with a single model and six synthetic task families. The paired materials change both guide and descriptions. Additional task families, separate wording ablations and observed developer integration are useful next checks.

If your team already uses [Promptfoo or Langfuse](competitive.md), evaluate whether an AdoptLab template or adapter fits the existing process. The standalone workspace adds an integrated feedback-to-revision path while keeping a deliberately small task catalog.

## Short demonstration script

1. Show the maintainer's question: did this onboarding change improve a defined first task?
2. Open an experiment and inspect one failure alongside a passing variant.
3. Explain the independent acceptance rule and the difference between valid output and correct input rejection.
4. Save a new material version, run the same task and associate the verified revision with feedback.
5. Export a report and show the limits: local operation, synthetic tasks, one model and pending human trials.

Use real saved results when recording. Label protocol demonstrations and automated runs. Request permission before recording participants or publishing their comments.
