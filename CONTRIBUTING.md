# Contributing

Begin with a reproducible synthetic task and its independently checkable outcome. Describe the user problem, current workflow, proposed change and tradeoff. Keep model experiments, protocol tests and human observations in separate reports.

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/check_public_tree.py --history
```

Changes to money/date/path rules require normal and error cases plus a hand-calculated oracle check. Materials create new immutable versions; keep frozen evaluation snapshots. Compare schemas/backends when evaluating wording changes. Record failed requests, cost bounds and task-family limitations.

Use the dedicated environment from [Quick start](README.md). Install `.[competitive]` only for Langfuse integration. Runtime files, test output and private local deliverables stay outside the committed source tree. Versioned reports referenced by the public evidence index retain their original denominators.

## Local product materials

`scripts/build_materials.py` generates three editable Word documents and two editable SVGs from the reviewed execution specification, the matching runtime database and the local OpenAPI contract. It requires `python-docx` and an existing Node.js runtime with `sharp`. Supply `--node` and `--sharp-module` when using bundled dependencies. Start the matching local application on port 8780 before generation.

```text
python scripts/build_materials.py --materials "MATERIALS_DIRECTORY" --runtime "MATCHING_RUNTIME_DIRECTORY" --node "NODE_EXECUTABLE" --sharp-module "SHARP_MODULE_DIRECTORY"
```

Replace the quoted paths with local directories/executables. The materials directory contains `AdoptLab材料执行方案.md`; the runtime contains the corresponding database. The generator renders the same SVG page frames into temporary previews and embeds fourteen figures in the PRD. After generation, update Word fields and its table of contents, render every page, check table pagination and cross references, and inspect both SVGs. Keep full Word documents local and publish only reviewed allowlisted selections. Tool paths belong in the private workspace guide.

Use synthetic data in issues and PRs. Never include keys, private documents, local user paths or identifiable participant information. See SECURITY.md. Human study invitations, consent and channel publication require the operator's explicit action.
