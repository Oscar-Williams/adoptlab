# Same-task competitive experience

Recorded 2026-09-30. Promptfoo 0.123.1 and Langfuse Python SDK 4.16.0 ran the same restricted MCP executor, model configuration, materials, synthetic records and independent oracle. This compares their custom-application evaluation workflows. Native Promptfoo MCP orchestration and Langfuse browser interaction remain separate, untested paths.

## T1 · Run A/B and inspect a failure

The paired cases are `task-01` and `task-11`, each with A/B. The final Promptfoo run reported 3/4 passing assertions, one failed assertion and zero provider errors, in 23 seconds at concurrency one. The final Langfuse experiment returned four items and an independent-contract average of 0.75. Each reported the invalid-input A failure; B correctly rejected it. These small runs validate adapters and inspection, without ranking provider intelligence.

Promptfoo's protocol control ran four checks: normal A/B, duplicate-ID rejection and deliberately corrupted summary output. All four assertions passed, including detecting corruption. The corrupted-output control is a deliberate test, separate from naturally occurring model failure.

## T2 · Configure, diagnose, revise and review

| Step | Promptfoo CLI experience | Langfuse SDK/cloud experience | AdoptLab local workflow |
|---|---|---|---|
| Setup | npm installation, explicit Python path, YAML plus custom Python provider; optional install scripts were left unapproved | User-created project keys, region URL, SDK and custom async task/evaluator | Independent Python environment, package installation, doctor and local service |
| Stable task | Python provider wraps shared MCP executor | Async task wraps the same executor | Task registry, immutable materials and stored hashes |
| Check failure | JavaScript assertions show the independent verdict and output reason in exported JSON | Independent evaluator scores task output; nested generations/tools reveal context | State, independent verdict, tool trace summary and re-verification |
| Revise | Change configuration or material reference and run evaluation again | Run a new experiment with the revised input/material reference | Create an immutable version, run the same task, link feedback to verified revision |
| Data exit | Local JSON report; sharing disabled | User-owned cloud project; local CLI readback audit | Allowlisted JSON and local cohort funnel |
| Cost | The custom provider returns a CNY cost upper bound in output; Promptfoo's automatic token/cost counters are not populated by this adapter | Generation usage is traced; local CNY ledger remains the reference rather than assuming cloud model-price matching | Per-request reservation includes retries and unknown network outcomes |

Observed integration friction: Windows TLS intermittently interrupted fetches. Langfuse's SDK executes task functions inside an event loop, so the initial synchronous `asyncio.run()` adapter failed; an async task fixed it. A network-dependent trace URL lookup initially disrupted one item after model completion; moving link generation outside task evaluation restored four complete items. Promptfoo needed an explicit independent Python executable. These are recorded integration conditions, without a claim that every user encounters them.

The cloud readback for a verified trace contains generations with model/usage and tools with input/output. Export masking and an actual-value audit found no DeepSeek/Langfuse secret key or personal path. SDK public routing metadata stays in private records. The final trace is kept in the operator's private audit, with no public project linkage here.

## Fit, overlap and tradeoff

Promptfoo suits teams already expressing tests and assertions as configuration; its broad provider and evaluation coverage is valuable. Langfuse suits teams wanting shared experiments, nested context and trace inspection; cloud project setup and a custom task remain part of the workflow. Both can implement much of AdoptLab's experiment logic through configuration and code.

AdoptLab's working hypothesis is reducing the setup and handoff between a material revision, a verified first task and developer feedback. Its integrated material editor, independent acceptance and feedback-to-run links provide a focused path. It accepts a narrower task catalog, one model integration, local operation and immature multi-user collaboration. Maintainer interviews and third-party installation will decide whether to retain a standalone product or package it as an integration/template.

## Adjacent products, pricing and channels

| Product | Official facts reviewed | Channel/entry evidence | Experience boundary |
|---|---|---|---|
| Promptfoo | [MCP integration](https://www.promptfoo.dev/docs/integrations/mcp/), [Community/Enterprise pricing](https://www.promptfoo.dev/pricing/) | [Getting started](https://www.promptfoo.dev/docs/getting-started/), [repository examples](https://github.com/promptfoo/promptfoo) lead technical readers to executable evaluations | Custom-provider checks completed; native MCP tests added in v0.3 below; paid features untested |
| Langfuse | [SDK experiments](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk), [cloud pricing](https://langfuse.com/pricing) | [Tracing start](https://langfuse.com/docs/observability/get-started), [repository](https://github.com/langfuse/langfuse) lead to project setup and first traces | SDK, cloud readback and authenticated GUI inspected; v0.3 observations below; no human usability ranking |
| PostHog | [Funnels](https://posthog.com/docs/product-analytics/funnels), [pricing](https://posthog.com/pricing) | [Product analytics docs](https://posthog.com/docs/product-analytics), [repository](https://github.com/PostHog/posthog) connect analytics users to event installation | Desk research; no conversion or traffic numbers inferred |
| Mintlify | [Assistant](https://www.mintlify.com/docs/assistant/index), [pricing](https://www.mintlify.com/pricing) | [Quickstart](https://www.mintlify.com/docs/quickstart), [documentation starter](https://github.com/mintlify/starter) connect maintainers to published docs | Desk research; assistant availability and paid experience not tested |
| Script + spreadsheet | Shared Python executor and exported trial table can serve the same small task | A developer's existing local workflow | Reference workflow implemented; collaborative handoff work requires maintainer observation |

Public pricing and available features need rechecking before purchase. No subscription was bought. Model costs are in the shared local ledger; hosted telemetry charges/quotas were not independently audited. Preparation/learning time was not rigorously timed, so it is not ranked. Public impressions, registration, activation and revenue remain unknown. Stars and issue activity supply community context, without conversion evidence.

### Pricing snapshot and adoption implications

Official pages rechecked 2026-09-30; USD figures below concern platform plans, separate from model inference and local infrastructure.

| Product | Published entry / next tier | Implication and unknowns |
|---|---|---|
| [Promptfoo](https://www.promptfoo.dev/pricing/) | Community is free, including local evaluations and custom integrations; red teaming has 10k probes/month. Enterprise and on-premise use custom quotes. | Local evaluation can start without buying collaboration features. Red-team limits concern that workflow; inference charges depend on providers. Paid collaboration was not tested. |
| [Langfuse](https://langfuse.com/pricing) | Hobby: free, 50k units/month, 30-day data access, two users. Core: $29/month, 100k included units and $8/100k additional units at the initial usage tier; 90-day access and unlimited users. | Cloud lowers infrastructure preparation; quotas, access windows and additional usage matter for repeated/team experiments. These are billable units, separate from model token costs. This project's billing screen was not audited. |
| [Mintlify](https://www.mintlify.com/pricing) | Starter, Pro and Enterprise are listed; Pro includes 10k AI credits/month, overage $0.01/credit. Assistant answers use 25 credits. | Documentation publishing and AI assistance have separate usage considerations. The retrieved page did not expose base plan amounts reliably; keep them unknown pending an interactive quote/view. No purchase or assistant trial. |
| [PostHog](https://posthog.com/pricing) | Usage-based product pricing and configurable billing limits; exact analytics free allowance and event tiers were not reliably present in the retrieved page. | Forecast using the selected product and current calculator. Desk research supports event/funnel overlap; implementation and invoice experience remain untested. |
| Script + spreadsheet / AdoptLab | Local reference workflow and original MIT code, with no product subscription; model execution is separately metered. | Setup and maintenance effort are real adoption costs. Human preparation time and willingness to pay require observation, beyond low inference expense. |

For a small team, a free entry alone does not settle the choice. Existing test infrastructure favors Promptfoo, shared trace inspection favors Langfuse, and published documentation favors Mintlify. AdoptLab needs maintainer evidence that its compact revision workflow saves enough preparation or handoff effort to justify another local tool.

## v0.2 workflow decision

The local product now connects material lineage, fixed task acceptance, metered MCP execution and feedback-linked re-verification. This is a workflow choice for small maintainers who need to decide which onboarding change to make. Existing evaluation and tracing tools remain useful for broader evaluation and observability. v0.2 does not claim that competitors lack these primitives; the contribution is the integrated task-and-revision contract with inspectable provenance. Independent maintainer interviews remain necessary to validate preparation cost and adoption barriers.


## v0.3 direct experience — 2026-10-02

These checks use the same synthetic record-processing contract and A/B materials. They test integration paths, with distinct completion criteria. They supply implementation evidence for the PRD; they provide no measured human setup-time advantage.

| Path and version | Actual execution | Outcome and interpretation | Product decision |
|---|---|---|---|
| Promptfoo 0.123.1 native `mcp` provider | Four direct tool assertions: list, read, valid normalization and duplicate rejection | 4/4 assertions pass. This provider tests tools directly; this test does not write the final task artifacts. | Keep tool health and complete-task acceptance as separately named outcomes. |
| Promptfoo 0.123.1 OpenAI-compatible model plus MCP | Four model cases, task-01/task-11 × A/B; host relay meters actual DeepSeek calls | Three first-tool calls succeed; one network outcome is unknown. Full task acceptance is 0/4. In this pinned integration path the provider returns after one tool-call round. The observation concerns this tested configuration, not all Promptfoo agent implementations. The local reservation ledger records CNY 0.045952 including unknown-outcome reservation. | AdoptLab retains a bounded multi-round task executor and independent artifact acceptance. Native provider checks remain useful for component tests. |
| Langfuse SDK 4.16.0, cloud GUI v4.49.0 | Four full MCP episodes; shared executor and independent evaluator; cloud readback and authenticated GUI | Final experiment has four items, independent-contract average 0.75. GUI shows task-11/A score 0.00 (`rejection_mismatch`), three scores 1.00, nested model/tool calls and token usage. An earlier executor-busy attempt has score 0.00 and is retained as integration failure. | Reuse Langfuse for trace inspection. AdoptLab provides explicit material lineage, local acceptance and revision handoff. |
| Manual Python + CSV | Four protocol cases, exported table, feedback-linked child material and same-condition retest | 4/4 task acceptance and verified revision. Protocol execution checks contract plumbing; it measures no language-model comprehension. | A script suits occasional checks. The workspace consolidates history, feedback and revision navigation for repeat use. |

Langfuse GUI route inspected: Experiments → latest experiment → four item scores → failing-item trace. The trace reveals `list_fixture_files`, `read_records`, `normalize_filter_records`, `write_outputs`, model generations and the independent rejection mismatch. `Annotate` and `Comment` are visible feedback actions; no annotation was submitted. In this project the new Tracing page, with its default root-observation filter, shows no rows while experiment item traces are accessible; the observed path uses Experiments. Experiment cost reads **not recorded**; local CNY usage accounting remains authoritative. Cloud item error count 0 does not imply task acceptance: the evaluator still returns 0 for an incorrect result.

SDK custom-application experiments executed the full task. The UI prompt-experiment feature has a different setup surface and was reviewed through [official documentation](https://langfuse.com/docs/evaluation/experiments/experiments-via-ui); no new cloud model connection was configured. This preserves a precise experience boundary.

The focused choice is a four-step developer entry feeding a maintainer's existing revision workspace. Broader providers and hosted trace collaboration remain strengths of the competing tools. Next validation asks whether maintainers value the integrated contract and handoff enough to adopt another local tool. Paid tiers, preparation time, willingness to pay and conversion are unmeasured.

Reproduction: `competitive/native_experience.py`, `competitive/manual_workflow.py`, `competitive/langfuse_experiment.py`, `scripts/langfuse_audit.py`. Model runs require the private local configuration and existing budget ledger; direct tools and the manual protocol baseline require no model credential. Private raw outputs remain outside the public build.
