# MCP profiles and task packages

AdoptLab compares developer onboarding materials against fixed task contracts. External servers run offline in pinned Linux containers over stdio. The built-in records example runs in its existing restricted Python process.

## Prepare the official Filesystem example

Install Docker with Linux containers, choose a data disk with sufficient free space, and confirm `docker info` succeeds. Configure `ADOPTLAB_DOCKER` in private local configuration if Docker is outside PATH. Then run:

```sh
adoptlab doctor
python scripts/prepare_filesystem.py
adoptlab run --config <config-path-printed-by-the-preparation-script>
adoptlab serve
```

The preparation script freezes upstream commit `f46d9578190b476b3501923ea8977d899e8db2cb`, adapts its Dockerfile with pinned base images and explicit dependency/build steps, and registers the resulting immutable image ID. A build downloads dependencies; experiment containers use `--pull=never` and have networking disabled. Source and images remain in local runtime storage. The fixed source records an MIT/Apache-2.0 licensing transition; retain its actual license rather than assigning a blanket MIT label: [source license](https://github.com/modelcontextprotocol/servers/blob/f46d9578190b476b3501923ea8977d899e8db2cb/LICENSE).

If Docker Hub is inaccessible, run `python scripts/prepare_filesystem.py --base-registry public.ecr.aws/docker/library`. Docker publishes official images through this AWS entry point. Both base images are pinned by repository digest. Image ID and source archive hash are recorded in private runtime evidence. The built image retains the generated dependency lock and upstream license.

The task reads a synthetic guide and writes independently checked JSON with a retry limit, endpoint and citation. Reference steps establish service correctness. Model execution receives the user instruction and input files; verification rules and reference steps remain outside the MCP container and model messages.

## Register your own task

1. Build and inspect a trusted MCP image. Record its immutable ID, source version and dependency lock.
2. Register a profile with `adoptlab register-profile --file profile.json`. Its `argv` is a list of arguments, and `tools` is an explicit allowlist. Profiles are local CLI registrations.
3. Use `examples/filesystem-task.json` as a task-contract example. Run `adoptlab check-task --file task.json`, then `adoptlab register-task --file task.json`.
4. Create a material whose description keys match the profile's tool allowlist. Choose the task and material in the workspace, or supply their IDs in a CLI run configuration.
5. Run protocol mode first. Add model mode after inspecting readiness, context and budget.

Task IDs and profile IDs are immutable. Use new IDs when changing a contract or profile. Input filenames must be relative, confined paths. Outputs are checked against `rules` separately. Rule operations are `exists`, `equals`, `contains`, `set_equals`, `range`, and `type`. JSON `path` is a sequence of object keys or array indices. Type names are Python JSON-value types such as `dict`, `list`, `str`, and `int`. File content is UTF-8, bounded to 1 MB per verification read.

Only stdio, offline input/output and allowlisted tools are supported in v0.2. Servers needing network access, device access, privileged mounts or additional host directories require a future reviewed execution profile.

## Trusted verifier extension

```sh
adoptlab register-verifier --id my-check-v1 --file trusted_check.py
```

This command installs explicitly trusted local Python code in private runtime storage. The script receives the output directory as its first argument and prints a JSON object containing `passed: true` or `passed: false`. It has a ten-second subprocess timeout and sanitized environment. It retains user-level permissions; operators must review the code before registration. The browser cannot upload executable code.

Reference the registered ID with `verifier` in a task package. Both declarative rules and the extension must pass. Extension content is frozen by hash. CLI verification and HTTP POST explicitly execute the registered extension; HTTP GET does not execute it.

## Interruption and evidence

`adoptlab history` lists recorded states. `adoptlab reconcile --run <id>` marks a recorded owner's dead process as interrupted. Unknown or live owners require operator review. No model request is automatically replayed. Unresolved charges retain their reservation.

Comparison checks execution conditions within each mode. Mixed backends, model configurations, verifier versions or tool schemas suppress aggregate verdicts. Material revisions link feedback to a successful same-task run with changed material and matching conditions.

Problem packages contain reviewed run metadata, hashes, independent verdicts and metered costs. Fixtures, local identities, feedback text and raw conversations remain private.
