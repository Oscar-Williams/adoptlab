# AdoptLab v0.4: onboarding, diagnosis and revision workbench

The primary user is an MCP tool maintainer who needs to turn integration friction into a reproducible material revision. A developer needs a first successful task and a useful failure handoff. A portfolio visitor needs independently inspectable evidence. These are workflow roles in a local, single-user application; they are not multi-tenant accounts.

## Product decisions

The existing stdio runner, task contracts, immutable materials, experiment settings, budget reservations and independent verifiers remain the foundation. FastAPI, Jinja2, native JavaScript, CSS and SQLite remain the implementation stack. The workspace now connects fourteen modules: overview, environment, catalog, task editor, experiment setup, comparison, history, run evidence, material versions, feedback/retests, release checks, first task, observations and public cases.

Structured execution records and acceptance rules are sufficient for the initial diagnostic workflow. Suggestions identify recorded failure categories; they do not prove a root cause. A successful run receives an acceptance explanation rather than failure advice. No additional repair agent, vector database or model request is required for diagnosis or preflight.

[Promptfoo's MCP server](https://www.promptfoo.dev/docs/integrations/mcp-server/) already exposes evaluation, comparison, assertions and configuration validation. [Langfuse datasets](https://langfuse.com/docs/evaluation/experiments/datasets) support repeatable experiments. AdoptLab's focus is the continuous relationship between integration materials, an exact failure, an immutable revision and its same-condition retest. It does not claim that competing tools lack evaluation capabilities. Sources checked 2026-10-07.

## Workflow and acceptance

| Module | Behavior and acceptance |
| --- | --- |
| Environment | Built-in, Filesystem and model checks separate mandatory from optional dependencies. A missing pinned image is reported before container execution. |
| Task editor | Import into editable fields, locate invalid rules, preflight without registration/execution, then register an immutable ID. Existing IDs cannot be silently changed. |
| Experiment | Show tasks × materials × repetitions, mode and frozen limits. A protocol reference plan is never sent to the model. |
| Evidence | Read recorded tool/error fingerprints, independent rules and retained artifacts. Artifact tampering fails re-verification. |
| Materials | Guide and tool descriptions form an immutable version, with parent and reason. Tool allowlists must match. |
| Feedback | Associate original run, feedback, changed material and accepted same-condition retest. Unverified changes cannot become verified revisions. |
| Release | Recheck the latest corresponding artifacts for a selected material/task set. Outcomes are passed, failed or insufficient; absent evidence never passes. Model runs also require known, matching responders. |
| Observations | Require consent, anonymous identifier, timezone-aware start/end, assistance level and evidence reference. Serialized duplicate insertion is idempotent; withdrawal removes observations. An entered source is an attestation, not verified external identity. |
| Public site | Three six-step interactive case walkthroughs, separate saved protocol evidence, historical reports and bilingual navigation. Visitors do not execute MCP or models. |

Protocol acceptance, model acceptance, automated role checks and actual observed sessions have separate denominators. A task-set release check is not a production reliability or adoption guarantee. Real-user benefits remain unknown. No external trial participant was contacted.

## Run locally

Use Python 3.11 or newer and an isolated runtime directory. On Windows PowerShell:

```powershell
python -m pip install -e ".[dev]"
$env:ADOPTLAB_RUNTIME = Join-Path (Get-Location) 'runtime/v04-workspace'
python -m uvicorn adoptlab.web:app --host 127.0.0.1 --port 8780
```

Open `http://127.0.0.1:8780/workspace`. Chinese is the default; the English switch preserves the active module. The first-task page needs no model credential or Docker. Filesystem tasks require Linux Docker, the locally available immutable image, a registered profile and matching material. Keep the execution service bound to loopback.

Prepare the official pinned Filesystem source using `python scripts/prepare_filesystem.py --profile-id filesystem-v04 --task-id docs-evidence-v04 --image-tag adoptlab-filesystem:v04`. The preparation script documents its upstream source and image. Use a fresh runtime, or choose new profile/task IDs if rebuilding changes an immutable image. Never overwrite a historical registration. The v0.4 local acceptance uses the separately pinned `filesystem-v04` profile and `docs-evidence-v04` / `docs-config-v04` task IDs. The document configuration example extracts exact values and a one-based source line; its independent rules check each field. For a later build, `ADOPTLAB_VALIDATION_TASK_SUFFIX` selects a fresh task suffix alongside the new profile/image settings.

`scripts/validate_workbench.py` expects the service on port 8780 and a locally built `adoptlab-filesystem:v04` image, unless `ADOPTLAB_VALIDATION_IMAGE` and `ADOPTLAB_VALIDATION_PROFILE` override them. It records three baseline/revised protocol pairs, feedback, revisions, release checks and a strict public projection. It does not spend model budget or count as human adoption. A changed image requires a new immutable profile and task IDs.

## Migration, recovery and publication

Database schema 3 adds release checks and observations. SQLite backup runs before migration; an existing backup is preserved and a new uniquely named backup is created. Future schemas are rejected. Historical runs, model charges and reports remain readable. Migration tests exercise a prior schema and retained experiment.

To consolidate reviewed local protocol evidence into an existing runtime, stop the execution service and run `python scripts/import_runtime.py --source <reviewed-runtime> --destination <historical-runtime>`. The importer rejects running tasks, nonterminal source records, invalid artifact IDs, symbolic links and conflicting immutable IDs. Historical queued records are retained without execution. It creates a uniquely named database backup, copies new run artifacts, inserts only new records in one transaction, checks foreign keys and preserves the budget ceiling. Credentials and runtime configuration are never copied. Keep the backup, artifacts and generated import manifest together for recovery.

The Windows consolidation on 2026-10-07 added 6 experiments and 20 runs, replacing zero historical rows. The historical charged/reserved upper bound remained CNY 3.963214, with 22 unresolved requests still reserved; four historical queued runs were preserved without replay. New upgrade checks used protocol mode and did not spend model budget. This bookkeeping value is not a measured adoption benefit.

Stop the local service before restoring a reviewed database backup. Preserve the current database and run artifacts first; never overwrite the only recovery copy. Restart with the matching code version. Interrupted runs are inspected/reconciled explicitly; unknown paid requests are not automatically replayed or released from reservations.

The default public landing page is the new Chinese case workspace. `experiments.html` retains the historical explorer and its original report denominators. `workbench.html` remains a direct case entry. The allowlisted Pages build publishes static assets only; it contains no database, execution service, credential, original fixture or observation free text. See [deployment](deployment.md) and [upgrade validation](../public-site/v04-validation.md).
