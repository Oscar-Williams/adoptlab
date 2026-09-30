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
| Promptfoo | [MCP integration](https://www.promptfoo.dev/docs/integrations/mcp/), [Community/Enterprise pricing](https://www.promptfoo.dev/pricing/) | [Getting started](https://www.promptfoo.dev/docs/getting-started/), [repository examples](https://github.com/promptfoo/promptfoo) lead technical readers to executable evaluations | CLI custom-provider checks completed; native MCP provider and paid features untested |
| Langfuse | [SDK experiments](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk), [cloud pricing](https://langfuse.com/pricing) | [Tracing start](https://langfuse.com/docs/observability/get-started), [repository](https://github.com/langfuse/langfuse) lead to project setup and first traces | SDK experiment and cloud readback completed; existing Edge page was unavailable through the browser connection, so no GUI usability ranking |
| PostHog | [Funnels](https://posthog.com/docs/product-analytics/funnels), [pricing](https://posthog.com/pricing) | [Product analytics docs](https://posthog.com/docs/product-analytics), [repository](https://github.com/PostHog/posthog) connect analytics users to event installation | Desk research; no conversion or traffic numbers inferred |
| Mintlify | [Assistant](https://www.mintlify.com/docs/assistant/index), [pricing](https://www.mintlify.com/pricing) | [Quickstart](https://www.mintlify.com/docs/quickstart), [documentation starter](https://github.com/mintlify/starter) connect maintainers to published docs | Desk research; assistant availability and paid experience not tested |
| Script + spreadsheet | Shared Python executor and exported trial table can serve the same small task | A developer's existing local workflow | Reference workflow implemented; collaborative handoff work requires maintainer observation |

Public pricing and available features need rechecking before purchase. No subscription was bought. Model costs are in the shared local ledger; hosted telemetry charges/quotas were not independently audited. Preparation/learning time was not rigorously timed, so it is not ranked. Public impressions, registration, activation and revenue remain unknown. Stars and issue activity supply community context, without conversion evidence.
