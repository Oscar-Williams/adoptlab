# Contributing

Begin with a reproducible synthetic task and its independently checkable outcome. Describe the user problem, current workflow, proposed change and tradeoff. Keep model experiments, protocol tests and human observations in separate reports.

```powershell
python -m pip install -e ".[dev,competitive]"
python -m pytest -q
python scripts/check_public_tree.py
```

Changes to money/date/path rules require normal and error cases plus a hand-calculated oracle check. Materials create new immutable versions; keep frozen evaluation snapshots. Compare schemas/backends when evaluating wording changes. Record failed requests, cost bounds and task-family limitations.

Use synthetic data in issues and PRs. Never include keys, private documents, local user paths or identifiable participant information. See SECURITY.md. Human study invitations, consent and channel publication require the operator's explicit action.
