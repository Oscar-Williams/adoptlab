# AdoptLab v0.2 decisions

The maintainer's job is to compare onboarding materials, inspect failure evidence and hand off a verified revision. The developer's job is to reach an independently accepted first result.

## Interface

The interface uses a quiet technical notebook: a primary execution workspace, a history strip and an evidence inspector. Status and lineage encode actual execution state. Colors retain the existing navy text, white surface, slate secondary text, teal action and red failure treatment. System sans-serif is used for content; monospace identifies contracts, tools and hashes. Feedback stays beside the evidence it describes. Motion is limited to changing execution status.

```text
Environment readiness
Experiment / task / material | Execution evidence
Run history                 | Verification / problem package
Material parent -> diff -> new version
Feedback -> successful changed-material run -> revision
```

## Execution

External MCP servers use pinned Linux container images over stdio, with offline fixtures and bounded output mounts. Model calls happen in the host application. The MCP container receives no model keys, reference rules or verifier code. Docker isolation reduces exposure; it is not a claim of protection against every kernel or container runtime vulnerability.

Trusted Python verifiers are explicitly installed by a local operator. Their subprocess receives a sanitized environment and a timeout. This is trusted local code with user-level permissions; the timeout is not an OS sandbox. A browser cannot install executable verifiers. Re-execution uses POST or CLI.

## Evidence

Old matrices remain historical evidence. Backend, tool schema, task, material, model configuration and verifier identity are recorded separately. Conditions are compared within execution modes. Mixed conditions remain visible and cannot produce an aggregate material verdict. Task families and repeated trials remain correlated; results describe the measured tasks and model.

The public site uses saved, reviewed evidence and local-only interactions. Demonstration state, simulated reviews and observed users use separate labels. Real independent user adoption remains an external validation step.
