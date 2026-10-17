---
title: "PPO Agent 07: Bundle the Experimental Serving Artifact"
date_created: 2026-10-17
tags: [design, ppo, deployment, artifact]
---

# Introduction

Make the trained 9×9 PPO opponent in [increment 07](07-trained-9x9-human-visible-slice.md) available from the deployable API image. For this experimental player, commit one frozen checkpoint and its manifest to source control, then ship them with the application. This is a companion implementation spec for 07, not a new training or strength milestone.

## 1. Scope and decision

Use `battle_agent_rl/artifacts/ppo_9x9_v3/` as the source-controlled serving directory. It contains exactly the selected `manifest.json` and `checkpoint.zip`; training runs, candidate checkpoints, evaluation output, and temporary files stay outside the repository. The committed files are the release artifact, not a recipe for generating new weights at container start or during deployment.

This increment supports only the existing `ppo_9x9_experimental` version-2 scenario, v3 policy contract, first-seat PPO player, and one immutable checkpoint. It does not promote the smoke-trained policy as a strong player, support Crossroads, redesign the API/PPO state boundary, cache model loads, or build a remote artifact registry. Those concerns retain their own gates.

## 2. Requirements

### REQ-001 — Select and commit a real artifact

- Produce a checkpoint with the existing `battle_agent_rl.ppo.multi_unit_train` entry point after at least one completed optimizer update. Use the exact v3 scenario and contract; do not commit initialized weights or an older 5×5/v1/v2 model.
- Reload and evaluate the candidate with the declared increment-07 seeds `1000..1019`, recording the training command, seed/configuration, actual timesteps, four outcome counts, checkpoint SHA-256, and source/runtime versions in documentation. This is connectivity evidence, not a skill threshold or held-out strength claim.
- Copy only the final manifest and its referenced checkpoint into `battle_agent_rl/artifacts/ppo_9x9_v3/`. Preserve their bytes and the manifest-listed digest. Do not hand-edit a manifest to make an incompatible checkpoint appear valid. Keep the selected artifact small enough for ordinary Git and CI checkout; if it is not, stop and review the packaging choice rather than silently adding Git LFS or a remote store.
- Treat this committed checkpoint as immutable while saved games can reference its digest. A future replacement must retain access to the old digest for existing games or explicitly define a migration/expiry policy; overwriting the files in place is not part of this increment.

### REQ-002 — Match the serving runtime

- Install the CPU PPO inference stack required by `MaskablePPO.load` in the API image. Pin the Python runtime and the exact Python, NumPy, PyTorch, Gymnasium, Stable-Baselines3, and SB3-Contrib versions checked by the existing manifest, using a reproducible ARM64-compatible installation. Training for the committed artifact and serving must use those same recorded versions. Do not relax compatibility checks simply to make the image load.
- Keep PPO dependencies out of `battle_hexes_core`. Do not train during the Docker build, image startup, or ECS deployment. The image may be larger than the present API image; verify its build and startup before changing ECS resources.
- Avoid adding a second, divergent version list. Document the training/serving environment and the dependency lock or exact pins in one maintainable place.

### REQ-003 — Bundle and configure the artifact

- The API Docker build must include the committed directory at a stable path and set `BATTLE_HEXES_PPO_RUN_DIR` to that path by default. An explicit administrator override may remain for local testing, but no production path may depend on `/tmp/opencode` or a developer's training run.
- Align `battle_hexes_api/dev.sh` and its README with the committed default; remove the stale, differing `/tmp` examples. Validate the configured directory, manifest, digest, scenario fingerprint, spaces, and software versions with the existing loader before accepting PPO game creation. Missing or incompatible artifacts fail clearly; never fall back to random or newly initialized weights.
- The client never chooses a checkpoint path. Keep the checkpoint digest bound to each created game as in 07. The artifact is packaged with the backend, not downloaded by the browser.

### REQ-004 — Prove the released image can serve it

- Build the API image for its deployed `linux/arm64` target, using the same Dockerfile and dependency pins as the release workflow. In a fresh container, verify the bundled files and checksum, load the model on CPU, create a PPO game through HTTP, issue at least one masked PPO order, and read the resulting game. Verify that an ordinary non-PPO game still works.
- Measure container startup and steady-state memory while loading and using the model. The current ECS task is 256 CPU / 512 MiB; change its resources only if measurement shows that allocation is insufficient, and validate the resulting CloudFormation template. Do not assume that passing host-Python tests proves the Fargate image fits.
- Keep the existing increment-07 acceptance gate: with a backend-connected browser and persistent repository, demonstrate a human/PPO game with mid-turn reload, visible fire/retreat, and a core-completed result. A mock UI smoke test or in-memory API test does not replace this gate.

## 3. Implementation boundaries

- `battle_agent_rl` owns the trained model, manifest, compatibility checks, and policy conversion. The API owns artifact configuration and serving orchestration. Core remains independent of PPO packages and artifact paths.
- Prefer the existing committed-image deployment pipeline over a new service, registry, startup download, or training job. Update the Dockerfile, dependency pins, developer launcher/docs, and relevant image tests; avoid unrelated refactoring of game rules or policy architecture in this change.
- A source-controlled artifact makes a specific experimental policy reproducible and available. It does **not** make that policy general across board sizes or unit rosters.

## 4. Acceptance criteria

1. A clean checkout contains the manifest and checkpoint; their digest, v3 contract, scenario fingerprint, spaces, and runtime versions validate without relying on a pre-existing temporary directory.
2. The ARM64 API image starts with no `BATTLE_HEXES_PPO_RUN_DIR` supplied externally and serves a PPO creation, one order, and subsequent GET. A missing/corrupt/wrong-version artifact fails explicitly rather than silently selecting other weights.
3. The image-level test records the artifact digest and measured memory; ECS resources are adequate or adjusted based on that evidence. Existing non-PPO creation and commands still pass.
4. `./server-side-checks.sh`, `npm run test-and-build`, and `./cloudformation-checks.sh` (if the template changes) pass. Increment 07 remains incomplete until its separate durable backend/browser playthrough is recorded.

## 5. Open Questions

No questions. This spec intentionally freezes one experimental checkpoint; the mechanism for promoting replacement models is deferred until there is a second model to serve.
