# Automatic website deployment

The GitHub repository contains both the local application and a complete, allowlisted evidence site in `public-site/`. Cloudflare Pages deploys only `dist/`. Its build uses Python's standard library; no package installation, database, model call or application secret is required.

## Cloudflare Pages Git integration

1. In Workers & Pages, create a **Pages** application and connect GitHub. Authorize access to the `Oscar-Williams/adoptlab` repository only.
2. Select repository `adoptlab`, production branch `main`, framework preset **None**.
3. Keep the root directory as the repository root. Set build command to `python3 scripts/build_static_site.py` and build output directory to `dist`.
4. Set `SKIP_DEPENDENCY_INSTALL=1` as a plain-text variable in both production and preview. Pages otherwise detects `pyproject.toml` and installs local application dependencies automatically. Save and deploy. Verify the generated Pages URL, English/Chinese switching, material/family filters, reports and MIT license.
5. In Custom domains, add `adoptlab.lukewilliams.top`. Follow the Pages DNS association process and check HTTPS. Keep other root-domain and email records unchanged.

Future pushes to `main` build and publish the saved evidence site. Preview branches can be enabled through Pages settings. Pages deployment and GitHub contract CI are independent by default; Pages does not wait for GitHub tests. Use protected branches with required checks when the team is ready to require verified merges.

The site serves recorded evidence. A source change does not regenerate model results. To publish a new experiment, review and sanitize its report, update the committed assets and results narrative together, and retain a versioned experiment protocol. Do not run paid experiments in the Pages build.

## Check locally

```powershell
python scripts/check_public_tree.py
python scripts/build_static_site.py
python -m http.server 8769 --bind 127.0.0.1 --directory dist
```

The build verifies its file allowlist, credential/private-path patterns and the versioned report schema, finite cost values and case conditions. Review a new experiment version together with its narrative and archive. The source repository's local credential configuration remains outside the repository. Set no DeepSeek or Langfuse key in Cloudflare Pages.

The live Python/MCP service remains local. Remote execution requires authentication, per-user isolation, queue/resource controls and separate security validation before publication.

Published endpoints: [custom domain](https://adoptlab.lukewilliams.top), [Pages mirror](https://adoptlab.pages.dev), [source](https://github.com/Oscar-Williams/adoptlab).

References checked 2026-10-01: [build image and dependency installation](https://developers.cloudflare.com/pages/configuration/build-image/), [Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/), [custom domains](https://developers.cloudflare.com/pages/configuration/custom-domains/).


## v0.3 publication boundary

The 16-file allowlist includes English/Chinese product PRDs and the v0.3 observation/retest ledger. The footer records the product version; the preserved experiment selector retains the v0.2 matrix and v0.1 archive. Before merging, inspect the Pages preview using `scripts/browser_public_check.py` and confirm its security headers, downloads, condition-matched comparisons and bilingual mobile layout. Run this acceptance again against the production custom domain after automatic deployment.
