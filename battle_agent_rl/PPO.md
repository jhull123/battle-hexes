# Battle Hexes PPO Agent

## Status

The 5×5 one-unit foundation (increments 01–05), 9×9 multi-unit prototype
(06), and experimental, 10-turn 9×9 PPO opponent (07) are complete. Increment
07 has trained checkpoints and a one-order-at-a-time API/web path; its deployed
browser acceptance run covered durable saved-state resume, visible fire and
combat retreat, and a displayed core-completed result. See the
[acceptance evidence](../specs/ppo-agent/evidence/07-dev-browser-acceptance-2026-10-24.md).
The [active schedule](../specs/ppo-agent/playable-player-schedule.md)
continues toward a Crossroads opponent; these 9×9 weights do not transfer to it.
Core remains authoritative for rules and results. Training uses SB3-Contrib
`MaskablePPO`; smoke training does not establish playing strength.

## Experimental trained 9×9 game (increment 07 complete)

One Git-tracked model per architecture lives in
`battle_agent_rl/archive/ppo/{x86_64,arm64}/`, each with `manifest.json` and
`checkpoint.zip`. From the repository root, with the Python 3.12 environment
from the [root README](../README.md#setting-up-the-api) activated:

```sh
./battle_agent_rl/train-ppo.sh          # replace the host architecture's model
./battle_agent_rl/train-ppo.sh arm64    # optional: ARM64 on x86 via Docker/QEMU
./battle_hexes_api/dev.sh              # serve the host architecture's model
```

The trainer requests 16 steps (seed 0, rollout 16, batch 8), requires legal
masked actions and updated weights, and replaces **only** the selected model.
On ARM64 hardware, training is native and requires Python 3.12 with the exact
serving library versions; a different Python patch version is allowed. The
x86-to-ARM64 command uses the pinned training image. To play, run
`npm run build && npm run serve` in `battle-hexes-web`, open
`http://localhost:4173`, and select **Elimination Demo 3 → Trained 9×9 PPO**.
PPO takes the first seat; Human, Random or Q-Learning takes the second.

`dev.sh` selects by host architecture; `BATTLE_HEXES_PPO_RUN_DIR` can override
it. The deployment image instead bundles the committed ARM64 model and **never
trains during build or deployment**. The manifest checks scenario, policy
contract, spaces, SHA-256, Python major/minor and exact library versions before
loading on CPU. The full training Python version stays in the manifest; a
different serving Python patch version logs a warning but still loads.
Architecture-specific library builds are not interchangeable.
Replacing either model expires saved games tied to its previous digest: GET
and orders fail with a clear server-log and browser message; they never use the
new weights silently. The default API store is in-memory and does not survive
a server restart; DynamoDB is needed for durable games.

The 9×9 v3 action is a unit slot plus row-major destination (162 actions).
Core-derived masks restrict each live decision; defensive fire resolves before
the next order, and combat runs once per side. The scenario has a 10-turn core
limit. A training/evaluation cutoff leaves core `in_progress`, not a draw.
See the [07 contract](../specs/ppo-agent/07-trained-9x9-human-visible-slice.md)
for observation fields, turn timing and persistence rules.

### Checkpoint evidence and replay

For each architecture, `archive/ppo/<architecture>/manifest.json` records the
checkpoint SHA-256, training configuration and runtime versions; the adjacent
`checkpoint.zip` is the artifact it identifies. Use
[`requirements-ppo-serving.txt`](../requirements-ppo-serving.txt) for serving
dependency pins and the Dockerfile for the ARM64 image's Python base. Native
ARM64 training may use another Python 3.12 patch version with matching library
versions. Do not copy checkpoint digests, version pins or replay counts into
this document: replacing a model can invalidate all three.

Replay each committed model on the declared seeds 1000–1019 in its matching
runtime, especially after retraining or changing game rules:

```sh
export PYTHONPATH="$PWD/battle_agent_rl/src:$PWD/battle_hexes_core/src"
python -m battle_agent_rl.ppo.multi_unit_evaluate \
  --run-dir battle_agent_rl/archive/ppo/x86_64 --seeds 1000:1020
# For ARM64 on x86, using the matching training image:
docker run --rm --platform linux/arm64 \
  -v "$PWD/battle_agent_rl/archive/ppo:/models" \
  --entrypoint python battle-hexes-ppo-training:arm64 \
  -m battle_agent_rl.ppo.multi_unit_evaluate \
  --run-dir /models/arm64 --seeds 1000:1020
```

Evaluation writes `evaluation.json` next to the model; it is ignored by Git,
not a third tracked artifact. Check its `checkpointDigest` against the
manifest and its per-seed episodes against the win/loss/draw/cutoff counts
before reporting results for that model. A short smoke run and replay are
integration evidence, **not** evidence of skill.

The [ARM64 image smoke check](../battle_hexes_api/README.md#arm64-deployment-image)
exercises the bundled model and ordinary play under the deployment task limit.
It does not measure production DynamoDB behavior or concurrency.

## Run locally

The earlier fixed **5×5** environment, trainer and core `PPOPlayer` are
separate from the playable 9×9 opponent. To inspect them from the repo root:

```sh
source .venv312/bin/activate
./inspect-ppo-rollout.sh --seed 0 --policy random --expect-ending completed
./inspect-ppo-rollout.sh --seed 42 --step-limit 1 --policy hold --expect-ending cutoff
./train-and-inspect-ppo.sh
```

The inspector needs no training dependencies; `./inspect-ppo-rollout.sh --help`
and `./train-and-inspect-ppo.sh --help` show options. The trainer smoke run
does not save a model by default. For a saved 5×5 experiment, use the commands
in [checkpoint evaluation](#checkpoint-evaluation) below.

## Checkpoint evaluation

The **5×5** trainer saves snapshots into a new `--run-dir`; the evaluator
selects a checkpoint on validation seeds and tests it on distinct held-out
seeds. With `.venv312` active, from the repo root:

```sh
export PYTHONPATH="$PWD/battle_agent_rl/src:$PWD/battle_hexes_core/src"
python -m battle_agent_rl.ppo.train --seed 0 --step-limit 50 \
  --total-timesteps 512 --n-steps 64 --batch-size 32 \
  --run-dir /tmp/ppo-5x5-run --checkpoint-interval 4
python -m battle_agent_rl.ppo.evaluate --run-dir /tmp/ppo-5x5-run
```

The fixed 512-step experiment selected the 256-step snapshot (validation
score 0.708). On 200 held-out seeds it scored 0.677; its paired score
difference against center-then-hold was **-0.087** (95% interval
[-0.160, -0.018]). The result does **not** support improvement over all
baselines. See [spec 04](../specs/ppo-agent/04-evaluation-and-checkpoints.md)
and the [foundation schedule](../specs/ppo-agent/implementation-schedule.md)
for selection protocol and evidence.

## Local core-game inference

With a selected 5×5 checkpoint, run
`python -m battle_agent_rl.ppo.local_game /tmp/ppo-5x5-run --seed 42`.
`PPOPlayer.from_checkpoint(...)` loads the frozen policy on CPU, validates its
scenario/contract/digest, and must be bound to the fixed game before play. It
never learns during a turn. See [spec 05](../specs/ppo-agent/05-inference-player.md)
for the Python interface and parity checks.

## Evidence and observation audit

The 5×5 observation contains row-major occupancy, defensive-fire readiness
and remaining steps; its core-derived mask includes legal destinations and
hold. Future rolls remain private. Uniform random play over seeds 0–99 won
36, lost 44 and drew 20. A step-limit cutoff is **not** a core draw; the
inspector audits observations and masks against core at each decision. See
[spec 02](../specs/ppo-agent/02-rollout-inspection.md) for the audit and
[spec 03](../specs/ppo-agent/03-masked-ppo-training.md) for reproducibility.

## Multi-unit prototype

Increment 06's fixed 9×9 v1 inspector is independent of both the 5×5 player
and the trained v3 game. Inspect it without trainer dependencies using
`python -m battle_agent_rl.ppo.multi_unit_inspection --seed 17 --cycle-limit 2 --policy random`
with `PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src`. The 162-action
slot/destination mask allows only pending living units' reachable cells;
cutoffs leave core in progress. See [spec 06](../specs/ppo-agent/06-multi-unit-design.md).

## Direction

Keep training and inference on the same observation/action contract, with
core responsible for rules and victory. The experimental 9×9 player is not a
Crossroads policy and should be hidden or retired when the evaluated
Crossroads opponent arrives. Follow the [active schedule](../specs/ppo-agent/playable-player-schedule.md);
strength work beyond that is deferred to [schedule 3](../specs/ppo-agent/crossroads-strength-schedule.md).
