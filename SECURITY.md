# Security and data boundaries

AdoptLab runs on localhost with synthetic fixtures. Keep `.env`, runtime databases, raw traces and personal research outside version control. The example environment has blank credentials. `doctor` reports presence, never values.

Tools expose listed fixture reads, deterministic transformation and fixed output filenames. The engine excludes credentials from its MCP subprocess environment. No shell or network tool is available. Relative path validation checks containment and Windows reparse points; this is not an OS sandbox for untrusted Python code.

The HTTP service validates local Host, same Origin for browser writes, JSON fields and body size. Validation errors omit rejected values. Task success is an internal server event. Feedback/material fields reject common key patterns. A local caller still has operator-level access; keep the service on loopback and use supervised demonstrations or tester-local installation.

Cloud tracing is opt-in and limited to the synthetic competitor workflow. Explicit payloads exclude headers, environment and free-form feedback. Masking runs before export; private readback audits check actual secret values and personal paths. Langfuse's own public project routing identifier can appear in SDK scope metadata. It stays in private readback, with no public report export.

Public reports use an allowlist. Raw tool artifacts and free text remain private. The Git hooks run `scripts/check_public_tree.py` without printing matches. Check ignored, tracked and historical content before any public release. Hooks are one layer; review staged changes and generated exports too.

For a vulnerability, prepare a minimal synthetic reproduction with version, platform and expected/actual behavior. Contact the maintainer privately through an agreed channel; do not put credentials or personal records in a public issue. Rotate a credential if it enters an unintended destination or public history.
