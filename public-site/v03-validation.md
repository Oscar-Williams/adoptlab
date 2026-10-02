# v0.3 validation and revision record

Recorded 2026-10-02. AdoptLab is an MCP onboarding verification and material-revision workspace for maintainers. The developer entry is check environment → execute first task → inspect independent acceptance → submit linked feedback. The maintainer retains registration, experiments, material editing, comparison and verified revision.

## Unified observation → decision → revision ledger

| ID / observed problem | User goal and severity | Decision / implementation | Recheck and boundary |
|---|---|---|---|
| P01 Developer view exposed experiment configuration | Complete a first task; high | Four-step developer page, fixed task-01/material B/protocol, history and retained context | D1/D3/D5: successful acceptance, linked feedback, refresh and bilingual mobile path |
| P02 Quick Start launched a matrix | Reach one inspectable result; high | `first-task` creates exactly one protocol run, verifies saved artifacts, returns failure exit code when acceptance fails | CLI test checks one experiment/run, zero model requests and tamper rejection; maintainer matrix remains available |
| P03 Raw environment JSON obscured requirements | Identify required conditions; medium | `doctor --target builtin/filesystem/model`; safe status/action fields | Builtin succeeds without Docker or credentials. Filesystem checks real container readiness; model checks private key presence without exposing its value |
| P04 Windows process handle survived termination | Resume after interrupted execution; high | Check `GetExitCodeProcess` instead of treating an open handle as proof of liveness | Windows regression test terminates a child, retains its handle and checks interrupted status. No paid request automatically restarts |
| P05 Old acceptance remained visible during rerun | Understand which run is being judged; high | Set checking state immediately, disable duplicate launch, restore the selected run after refresh | D2 checks deliberate artifact corruption and explicit fresh execution |
| P06 Task selection raced material loading | Execute the selected external contract; high | Version asynchronous material loads; disable launch until matching context is loaded | M2/D4 run the registered official Filesystem container contract and verify it |
| P07 Verification of interrupted/no-artifact runs could raise server error | Understand missing outputs; medium | `ARTIFACTS_UNAVAILABLE` precheck with safe HTTP 400 | API regression covers missing manifests; no stale acceptance |
| P08 Feedback lacked immediate handoff context | Deliver an actionable report; medium | Link exact experiment/run and recover associated feedback in maintainer view | D1 handoff and M1/M2/M3 child-material retests |

The issue ledger joins product observations, engineering checks and review outcomes in one process. Each record retains executor/source metadata. Automated elapsed durations measure script execution; no human setup-time improvement is inferred.

## Eight role walkthroughs

| M1 · AI API maintainer | Immutable material revision → Comparable verified retest → Feedback-to-revision lineage | passed |
| M2 · MCP maintainer | Immutable material revision → Comparable verified retest → Feedback-to-revision lineage | passed |
| M3 · Documentation owner | Immutable material revision → Comparable verified retest → Feedback-to-revision lineage | passed |
| D1 · New Python developer | Single task starts without experiment configuration → Independent artifact verification → Run and feedback recover after refresh → Maintainer receives exact run and feedback | passed |
| D2 · Experienced MCP developer | Single task starts without experiment configuration → Independent artifact verification → Run and feedback recover after refresh → Tampered output is detected → Explicit new run succeeds | passed |
| D3 · Windows developer | Single task starts without experiment configuration → Independent artifact verification → Run and feedback recover after refresh → Sensitive feedback blocked | passed |
| D4 · Container developer | Single task starts without experiment configuration → Independent artifact verification → Run and feedback recover after refresh → Registered external container prerequisites ready → Official Filesystem container task accepted | passed |
| D5 · English documentation reader | Single task starts without experiment configuration → Independent artifact verification → Run and feedback recover after refresh → Keyboard and mobile path | passed |

Source: Codex-simulated roles, operated through real application UI and actual local execution. Eight scenarios passed; page errors: none. External human participants and sessions: zero. Evidence includes private screenshots, run IDs, CSV and JSON from `scripts/review_v03.py`. Public records omit local paths and raw conversation. These scenarios validate workflow behavior and identify obstacles; willingness to adopt remains a research hypothesis.

Three maintainer roles each save feedback, create an immutable child material, execute a comparable retest and mark the accepted revision. Developer scenarios cover first use, experienced artifact checking, Windows credential-free setup, real container continuation and English mobile/keyboard use. D3 attempts sensitive feedback and confirms rejection.

## Direct competitive checks

[Competitor experience](competitive.md) records native Promptfoo tool tests, its tested model/tool integration path, actual Langfuse SDK/GUI inspection and a manual CSV baseline. Native tool assertions pass 4/4; four native model cases reach three first-tool successes and one network-unknown outcome, with 0/4 complete-contract acceptance in the pinned one-round integration. Langfuse's four full tasks score 3/4; manual protocol tasks pass 4/4 and verify a material revision. Different execution paths are labeled explicitly; these results supply product tradeoffs rather than an overall ranking.

## Acceptance and historical evidence

Local regression completed: **44 passed, 2 skipped**. A fresh F-drive Python 3.11 venv installed the base package and completed `doctor --target builtin` and `first-task` with zero model requests and independent artifact/hash acceptance. Nine static browser checks passed with no page errors; the public-tree scan found zero issues across 107 candidate files. The reviewed build contains 16 allowlisted files.

Run `python -m pytest -q`, `adoptlab doctor --target builtin`, `adoptlab first-task`, `python scripts/check_public_tree.py`, `python scripts/build_static_site.py`, and the browser acceptance scripts. CI installs on Windows/Linux, performs the first task and runs the actual offline Filesystem integration on Linux. Target-aware checks and artifact verification have regression coverage for missing dependencies/configuration, unwritable runtime, cancellation and tampering; existing timeout, budget, state and revision tests remain in the suite.

The frozen v0.2 report retains 48 protocol executions (48 accepted) and 144 model experiments (130 accepted). The v0.1 archive retains 72 model episodes. v0.3 checks are separate records and do not rewrite these historical denominators. New model competitor runs use the existing cost ledger; unknown network outcomes retain reserved upper cost. The inference executor and oracle were preserved, so the 144-case matrix was not rerun for the UI revision.

## Delivery and next observation

Public deliverables include the English/Chinese PRD, tutorial, measured comparison, this ledger, preserved reports and offline explorer. Public Pages serves reviewed saved evidence; MCP execution and private credentials stay local. Release acceptance checks downloads, report pairing, historical evidence, reload errors, bilingual mobile layout and hosted security headers.

The next external observation uses the same ledger: consent, actual executor, first-seen version, assistance, acceptance, friction and revision follow-up. Prepared invitation and observation templates remain available in the research kit. Actual people and adoption metrics are updated only from observable participation records. A supported product narrative is problem → competitor choice → contract → implementation → observed obstacle → revision → retest → release.
