# AdoptLab 0.5 validation

Recorded 2026-10-12. Product version 0.5.0, schema 4. The release PR links the exact commit and hosted CI results.

## Local engineering validation

The Windows suite passed 57 tests with 2 platform-permission skips. Tests cover transactional concurrent feedback retries, idempotency conflicts, revision-time evidence verification, stale artifact detection, schema-3 migration, repeated settlement and invalid JSON positions. Existing cancellation, timeout, budget, privacy, observation and release checks remain in the suite.

Three cases completed two real protocol runs each in experiment `13dd17e6f2774113b17d70e93e8b20f1`: `task-01`, `docs-evidence-v05`, `docs-config-v05`. All six outputs passed independent acceptance; each pair includes feedback, an immutable material revision, same-condition retest and release check. The pinned Filesystem image was available and executed the external tasks.

[Current protocol report](workbench-evidence.json) retains run, condition, task, material and artifact fingerprints. [The v0.4 report](workbench-evidence-v04.json) and [historical model matrix](report.json) retain their original scope. Both sides of the new protocol pairs pass; these pairs demonstrate an executable revision workflow. New model expense is zero. Human observations remain zero; adoption benefit is unknown.

## Materials and design

Three editable Word documents are delivered locally: user needs, solution decisions and detailed PRD. Selected editable [prototypes](prototype-selected.svg) and [business/AI workflow](workflow-selected.svg) are public. IDs map to the local PRD. Full documents and private runtime data stay local.

Figma task editor, comparison and revision specifications were updated in Chinese and English; six updated screens were exported and prototype flow roots were read back. The updated comparison and revision nodes were independently opened through the cloud file in the existing Edge browser; cloud-view screenshots are retained locally. The public walkthrough remains a labeled demonstration; it does not execute visitor tools or models.

## Migration and recovery

The canonical project and runtime were copied to the consolidated workspace. All 1,746 migrated runtime files matched their source SHA-256; 358 historical runs were retained and SQLite integrity passed. Schema 4 adds submissions and revision evidence after a consistent backup. The consolidated workspace is the development entry. Existing version materials remain in its archive; the active Docker disk and current pinned image support future runs. Credentials and full local Word documents are excluded from publication.

## Publication gate

Windows, Linux and real container CI must pass on the candidate branch before merge. The public site contains only allowlisted static assets and sanitized reports. Formal-domain checks verify the current report and downloads after deployment. Actual participants and model improvements require their own supporting evidence.


## Maintainer workflow refinement

The overview explains the product purpose and the maintainer, developer and case-reader paths. Filesystem readiness checks target a selected profile. Experiment submission checks task and material tool compatibility before creating an experiment. Material editing and release checks inherit the selected run. Feedback revision choices list accepted same-task, same-mode runs with a new material; the backend rechecks full conditions and artifacts. Release exports preserve the original decision and include current verification of the exact recorded runs. Local regression: 58 passed, 2 platform-specific skips. Candidate CI and formal publication are separate release gates.

The local PRD embeds fourteen numbered prototype figures and traces six scenarios to functions, nodes, acceptance rules and evidence. The editable node SVG keeps the main workflow and recovery branches; detailed node choices, failures and optimization are in the PRD. Current-tree scanning checked 143 candidate files and credential scanning checked 250 unique reachable historical blobs with zero findings. An isolated README smoke task passed independent verification with zero model requests. Fourteen English modules and the developer/public entry paths at 1440, 1024 and 390 widths loaded without horizontal overflow in the existing Edge session. The updated Figma overview was independently opened from its cloud prototype.
