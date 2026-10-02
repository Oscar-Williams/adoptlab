# Evidence index: from onboarding question to verified revision

AdoptLab's maintainer task is to determine which onboarding material helps a defined first task, inspect failure evidence and hand off a verifiable change. The developer task is to complete that first task with usable setup guidance and independent acceptance.

| Product decision | Implemented mechanism | Reproduction / evidence | Interpretation |
|---|---|---|---|
| Keep task success explicit | Immutable task packages, declarative rules and trusted verifier registration | [Task packages](mcp-task-packages.md), verifier tests | Task acceptance is independent of model self-report |
| Compare wording under fixed conditions | Guide × description factorial, frozen conditions and task-family splits | [Experiment](experiment-results.md), [validation](v02-validation.md) | 48 protocol checks and 144 synthetic model episodes; small correlated sample |
| Support a second tool backend | Pinned offline Filesystem profile, nonroot container and mount controls | [Integration guide](mcp-task-packages.md), Linux container CI | Local stdio/offline interoperability; hosted arbitrary execution remains outside this release |
| Make feedback actionable | Run-linked feedback, immutable child material, same-condition successful revision and safe problem package | [Architecture decisions](v02-decisions.md), workflow browser script | Three additional simulated maintainer loops verify the mechanism |
| Improve evidence navigation | Separate modes/cohorts/splits, archived report and checked saved comparison | Public explorer and public browser acceptance | Shows recorded comparisons; human adoption is unmeasured |
| Turn review into iteration | Prioritized concern, implementation change and regression evidence | [Review record](review-results.md) | Eight Codex-simulated roles; zero observed participants |
| Make delivery repeatable | Windows tests, Linux container checks, allowlisted Pages build and preview-first release | GitHub Actions and [deployment](deployment.md) | Release checks belong to the actual commit |

Original AdoptLab contributions cover the product workflow, records MCP tools, acceptance contracts, material lineage, execution budget/state governance, public evidence explorer and reviewed adaptations. Upstream roles and licenses are retained in NOTICE and the pinned integration documentation. Codex assists implementation, debugging, documentation and simulated review; automated and simulated execution are separately labeled.

A supported project account follows: onboarding problem → contract and execution boundary → competing workflow comparison → product choice → implementation → measured task evidence → reviewed obstacle → revision and retest → published version. The next external milestone is actual maintainer observation and independent developer use. Record consent, task/version, outcome, assistance and revision follow-up before claiming human adoption, time saved or growth.


## v0.3 first-success product iteration

- Baseline scope and acceptance: [English PRD](product-prd.md), [中文 PRD](product-prd.zh-CN.md).
- Measured product alternatives: [native Promptfoo, Langfuse SDK/GUI and manual baseline](competitive.md#v03-direct-experience--2026-10-02).
- Unified issue/decision/retest chain: [v0.3 validation](v03-validation.md).
- Developer delivery: `first-task`, target-aware doctor, four-step bilingual page, safe artifact verification and exact-run feedback handoff.
- Reliability: Windows dead-process recovery, asynchronous task/material consistency and safe missing-artifact errors.
- Historical experiment claims remain 48 protocol/144 model episodes. Eight v0.3 role walkthroughs are simulated execution; real external adoption remains unmeasured.
