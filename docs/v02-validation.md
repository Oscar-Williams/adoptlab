# AdoptLab v0.2 validation

Local implementation and measurements were completed on 2026-10-01. The v0.2 publication bundle contains 192 saved executions, including 48 protocol checks and 144 model trials. The original 72-episode report is retained as a historical download. Deployment checks are recorded separately in the release record.

## New mechanisms

- Immutable offline MCP profiles with pinned container images, task packages and independent declarative acceptance.
- Explicitly registered trusted Python extensions with integrity checks and bounded subprocess execution.
- Material parent/name/reason metadata and unified diffs; same-task, changed-material, terminal-success revision verification.
- Persistent run selection, history filters, feedback handoff, configuration copying and safe problem packages.
- Saved execution limits, separate backend/verifier/tool fingerprints, condition checks and explicit interruption reconciliation.
- Versioned public report validation and local-only evidence walkthrough.

## Frozen factorial

The new matrix contains twelve synthetic tasks, four guide/description combinations and three model trials: 144 model episodes. Another 48 protocol executions checked the four combinations without model calls; all 48 passed.

| Guide | Tool descriptions | Model task acceptance |
|---|---|---|
| A | A | 23/36 |
| A | B | 35/36 |
| B | A | 36/36 |
| B | B | 36/36 |

One A/B episode failed before any model response was recorded. Its responder remains unknown, and its failure remains in the denominator. All observed responses reported `deepseek-flash`. Network uncertainty retains reservations; costs represent conservative upper bounds rather than provider invoice amounts.

The guide main effect is +19.44 percentage points, description main effect +16.67 points, and interaction −33.33 points on the measured task-acceptance scale. A negative interaction here reflects overlap in the improvements relative to the additive contrast. Six task-family clusters provide exploratory bootstrap intervals; this small synthetic sample supports inspection and follow-up experiments. It does not establish general model performance or independent developer adoption.

Exploration families were threshold, whitespace and currency; held-out families were timezone, empty output and invalid input. No material was tuned from held-out outcomes. Correlated repeated trials remain identified in the raw records.

## External MCP

The official Filesystem source is frozen at `f46d9578190b476b3501923ea8977d899e8db2cb`. A deterministic two-tool baseline and a real-model document-evidence task both passed four independent acceptance rules and artifact re-verification.

Eleven runtime checks passed: model task contract, independent re-verification, forbidden read, read-only input, path traversal rejection, disabled network, read-only root, nonroot user, dropped capabilities, mount allowlist and absent model/tracing credentials inside the container.

The source is unchanged. The build adaptation pins Node base images, uses explicit dependency/build steps and retains the actual MIT/Apache-2.0 transition license. Docker Official Images were retrieved through their AWS ECR entry point after Docker Hub authentication traffic failed. Source archive and image hashes remain in runtime evidence.

## Reproduction and evidence boundaries

The final local suite passed 34 tests. One Windows symbolic-link test was skipped because the current process lacks symlink creation privilege; junction checks and actual container path-restriction checks passed. A fresh Python virtual environment installed the wheel and passed 24/24 records protocol tasks.

```sh
python -m pytest -q
python scripts/browser_check.py
python scripts/run_v02_matrix.py
python scripts/analyze_v02.py
python scripts/prepare_filesystem.py
python scripts/verify_filesystem.py
python scripts/check_public_tree.py
python scripts/build_static_site.py
```

Browser automation completed the create/run/feedback/material-change/revision/reverify workflow in installed Edge, with English, Chinese and mobile checks. These runs are labeled automation and contain zero observed human participants.

Additional browser acceptance passed run-selection restoration, history browsing, persisted feedback handoff, external container execution and the bilingual mobile saved-result walkthrough. JavaScript syntax checks passed. Public-tree scans and the versioned static build are release gates. The v2 export includes terminal state, execution mode, cohort, task split, condition fingerprint and responder; the walkthrough excludes unknown-responder or condition-mismatched pairs.

Private runtime artifacts include the frozen protocol, complete factorial report, analysis, container source manifest, isolation validation and browser screenshots. They remain outside Git. Published summaries contain counts and mechanisms; private credentials, personal paths, fixtures and raw conversations are excluded.

Real maintainer interviews, independent user observations and channel conversion evidence remain external validation tasks. Earlier role reviews were generated by Codex simulation and retain their simulation label.
