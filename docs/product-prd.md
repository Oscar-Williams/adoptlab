# AdoptLab product baseline · v0.3

Recorded 2026-10-02. Product scope and acceptance are versioned alongside implementation. [中文](product-prd.zh-CN.md).

## User, problem and first value

AdoptLab is a local MCP onboarding verification and material-revision workspace for small tool-maintainer teams. Its core decision is: **which onboarding change should we make, and what evidence supports accepting it?** Developers complete a bounded first task and share actionable friction; maintainers compare guides/tool descriptions, inspect independent acceptance, revise and recheck.

The supported users are MCP maintainers, documentation owners and developers integrating a registered tool. AI API teams exposing MCP are a possible customer segment; generic API onboarding remains an expansion hypothesis. User interviews, preparation-time savings, willingness to pay and independent adoption remain unvalidated.

Two local tasks establish scope: synthetic records normalization and official Filesystem document evidence extraction. The public website offers a saved-evidence walkthrough; installation enables actual tool execution. This architecture keeps credentials and execution governance local while making outcomes inspectable.

## Baseline evidence and competing workflows

v0.2 retained 48 protocol checks and 144 model episodes; model acceptance was 130/144 under the frozen conditions. These establish mechanisms and exploratory material effects. They do not measure human onboarding success. Existing Promptfoo and Langfuse adapters exercise the same executor. [Competitive experience](competitive.md) records native integration checks and workflow tradeoffs.

The v0.2 developer page presented experiment creation, task selection and material editing together. The Quick Start configuration selected twelve tasks and two materials. Environment checks returned raw JSON and a runtime path. These inspectable implementation facts justify a shorter first-task path and clearer readiness; developer preference remains a research question.

## Product task and acceptance

1. **Prepare:** install in an independent Python environment, select a writable runtime directory, inspect required checks. Built-in protocol execution needs Python/dependencies/storage; Docker and model credentials are later capabilities.
2. **Execute:** start task-01 with material B, protocol mode and one trial. The same bounded engine and original four MCP tools execute synthetic inputs.
3. **Understand:** see terminal status, tool/model counts, cost, contract verdict and next action. Re-verify saved artifacts and inspect hashes; preserve failures and cancellations.
4. **Report:** attach feedback to the exact task, run and material; download an allowlisted report/problem package. Remove credentials and personal details from feedback.
5. **Revise:** open the maintainer workspace with the selected run and feedback, save an immutable material with reason and lineage, execute comparable conditions and validate the revision.

The first-task CLI stores a report and verification summary. The browser executes through existing run APIs and restores local selection after refresh. CLI automation and browser instances carry explicit execution provenance. A successful reference workflow establishes protocol/artifact correctness; material effects on model behavior use model experiments.

## Priority and decisions

| Priority | Problem evidence | Decision and implemented boundary | Acceptance |
|---|---|---|---|
| P0 | Default Quick Start starts a 24-run configuration | Add one-task CLI; retain the complete matrix command | One protocol run, zero model requests, independently accepted artifacts |
| P0 | Developer sees maintainer controls | Dedicated four-step page; maintainer keeps experiment/history/editor features | Start without naming an experiment; provide evidence and feedback |
| P0 | Raw readiness mixes capabilities | Target-specific required/recommended checks; browser responses omit private paths | Missing Docker/API/tracing does not block built-in first task |
| P0 | Feedback handoff loses selected context | Explicit run/experiment deep link, matching feedback lookup | Maintainer sees the developer's exact execution and feedback |
| P1 | Windows terminated process can retain an open handle | Check process exit status before reconciliation | Dead owner becomes interrupted; unresolved reservations stay retained |
| P1 | New run briefly shows previous success | Set checking state and disable duplicate start while submitting | New execution shows current status and explicit errors |
| P1 | Cancelled run may have no artifacts | Allow terminal feedback; enable re-verification only for retained result | Cancellation remains explainable and feedback stays linked |
| P2 | Broader deployment/collaboration needs | Keep remote execution, arbitrary tools and multi-user work outside this release | Public bundle contains reviewed static data only |

## Measurement and next decisions

| Metric | Definition | Evidence boundary |
|---|---|---|
| Task acceptance | Successful terminal execution plus independent contract pass | Report by task/mode/version; retain failures |
| First successful task | First accepted task following a documented installation/start | Automated checks currently demonstrate path correctness |
| Time to first value | Participant's observed start through first accepted result | Capture only in an actual observed session; automated elapsed time is separate |
| Handoff completeness | Run/material/feedback/change/retest linkage present | Review the saved lineage and comparable conditions |
| Independent completion | Participant completes the task with recorded assistance | External participants and sessions currently zero |
| Adoption and return | Consented, ordered first-task/return events with known source | Public static hosting requests supply no adoption denominator |

Successful role checks justify shipping the improved path. Real observed sessions should determine whether instructions remain unclear, whether maintainers prefer an integration/template, and whether a second task is useful. Preserve assistance, learning effects and negative findings. Pricing, team subscriptions and growth channels remain hypotheses until validated.

## Traceability and release

[Unified review and retest](v03-validation.md) · [Decision/evidence index](evidence-index.md) · [Architecture](architecture.md). Public documentation contains decisions and reviewed summaries; screenshots, local IDs, contact details and raw cloud readbacks stay in private runtime records. Original modules and retained third-party licenses remain identifiable.
