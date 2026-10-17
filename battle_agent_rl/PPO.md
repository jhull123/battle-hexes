# Battle Hexes PPO Agent

## Status

The fixed 5×5, one-unit-per-side environment, seeded rollout inspector,
masked PPO training loop, checkpoint evaluation and core-compatible inference
player are implemented. A separate 9×9 multi-unit decision prototype is also
implemented (see the
[schedule](../specs/ppo-agent/implementation-schedule.md)).
An experimental 10-turn, core-loaded 9×9 v3 slice now has bounded masked
training, frozen checkpoint replay, and a one-order-at-a-time API/web path.
Increment 07 is **not yet marked complete**: the required backend-connected
browser demonstration with durable storage, mid-turn reload, visible fire and
a displayed completed result has not been recorded.
Increments 01–06 are completed foundation work; the
[active playable-player schedule](../specs/ppo-agent/playable-player-schedule.md)
begins at 07 with bounded 9×9 multi-unit smoke training and a human-visible
game against its saved, reloaded checkpoint. It ends with a selectable
human-versus-PPO Crossroads game.
Core owns game rules; PPO uses SB3-Contrib `MaskablePPO` to learn legal
destinations. The fixed-protocol held-out comparison does not support
improvement over all baselines; the inference player does not change that
finding.

## Run locally

Use Python 3.12. From the repository root, after setting up `.venv312` as in
the [root README](../README.md#setting-up-the-api):

```sh
source .venv312/bin/activate
./inspect-ppo-rollout.sh --seed 0 --policy random --expect-ending completed
./inspect-ppo-rollout.sh --seed 42 --step-limit 1 --policy hold --expect-ending cutoff
./train-and-inspect-ppo.sh
```

The inspector does not need trainer dependencies; run
`./inspect-ppo-rollout.sh --help` for options. `random` samples sorted legal
indexes with a policy-local `random.Random(seed)` separate from the game RNG;
`hold` keeps the learner in place. The trace shows the pre-action board,
observation, legal indexes/coordinates, action, defensive fire, combat, reward
and final state. `L` is learner, `O` opponent, `.` empty and `*` the chosen
destination, which can differ from the post-combat unit position. A cutoff
leaves core status in progress. `NO_COLOR=1` disables styling.

`./train-and-inspect-ppo.sh` runs the verified short masked-PPO smoke training
(seed 0, four-step limit, 32 timesteps, rollout 16, batch size 8), then
inspects episode seed 42. It uses the repo's `.venv312` automatically when
present; from an isolated worktree, activate a Python 3.12 environment first.
Pass trainer options after the script name to override the defaults. For
example, `./train-and-inspect-ppo.sh --total-timesteps 256 --n-steps 64
--batch-size 32 --step-limit 50` runs a longer inspection. PPO dependencies
must be installed as described in the root README.

The environment's row-major 25-cell observation has `occupancy` (learner 1,
opponent -1, empty 0), `defensive_fire_ready` (0/1) and `remaining_steps`.
The boolean action mask marks legal destinations; the current cell is hold.
Rewards are +1 for a win, -1 for a loss and 0 otherwise. At an ending the mask
is all false; a step-limit cutoff is `truncated`, not a core draw. The Gym
adapter (`ppo.gym_env.MaskedBattleHexesEnv`) exposes the same inputs to
`MultiInputPolicy`. Always pass the current mask for prediction:
`model.predict(obs, action_masks=env.action_masks(), deterministic=True)`.

The 5×5 layout is a fixed row-major encoding of hex cells, not square-grid
movement: core computes hex reachability and paths, and the mask prevents
illegal destinations. The current MLP does not explicitly receive hex-neighbor
or distance features, though, so it must learn useful spatial relationships
from experience. Keep this simple representation as the first baseline; the
32-timestep smoke run only verifies plumbing, not playing strength. Evaluate
on held-out seeds against random and hold before changing it. If learning
stalls or is too sample-hungry, try explicit hex-aware features (for example,
distance to the opponent) before moving to a graph-based policy. Revisit the
representation when adding larger or variable-sized boards.

The trainer uses one CPU environment and a seeded random opponent. Explicit
`reset(seed=s)` starts game seed `s`; automatic resets advance to `s+1`,
`s+2`, etc. The Gym action space is seeded too. The CLI requires positive
`--step-limit` and `--total-timesteps`, `--n-steps > 1`, and
`1 < --batch-size <= --n-steps`; the values above are its defaults. It reports
actual collected steps (which may exceed the request), completed episode
outcomes/length/return and PPO update losses. Losses do not measure playing
skill. Optional `--inspect-episode SEED` uses the just-trained in-memory model
for one deterministic, mask-aware episode, bounded by `--step-limit`. It prints
each board, legal index and coordinate, selected action, reward and ending
through the same audited inspector as the random/hold baseline. The supplied
seed makes this spot check repeatable; without `--run-dir` the model is not
saved. Compare two identical training commands' summaries
and inspection traces, and inspect decisions where most destinations are
illegal: every printed PPO action must appear in that decision's legal list.

## Checkpoint evaluation

From the repository root with `.venv312` active and the PPO dependencies
installed, run (the directory must not already exist):

```sh
export PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m battle_agent_rl.ppo.train --seed 0 --step-limit 50 --total-timesteps 512 --n-steps 64 --batch-size 32 --run-dir /tmp/ppo-run --checkpoint-interval 4
python -m battle_agent_rl.ppo.evaluate --run-dir /tmp/ppo-run
python -m battle_agent_rl.ppo.evaluate --run-dir /tmp/ppo-run --checkpoint checkpoint-000000256.zip --split validation
```

`--checkpoint-interval` counts completed optimizer updates; a snapshot is
also saved at the final update. Training is one uninterrupted `learn` run.
`--run-dir` creates a new directory, preventing accidental overwrite. For
alternate, predeclared sets, pass `--seed-lists FILE` *at training time*;
the JSON file has ordered integer arrays `validation` and `held_out`.
Defaults are 1,000,000–1,000,199 and 2,000,000–2,000,199. The run manifest
records the complete lists, training episode seeds (including the unfinished
episode), training configuration, completed-update interval, step limit,
CPU/software versions, fixed policy-input contract, baselines, selection rule,
and `.zip` checkpoint paths, update positions, and SHA-256 digests. A changed
step limit, policy-input space, contract or software version rejects reload.
The replay command reloads a checkpoint without training. Held-out replay is
restricted to the already selected checkpoint.

`validation-episodes.json` and `validation-table.txt` contain all candidate
results ordered by collected timesteps; `validation-report.json` records the
selection. Only the highest validation game score advances, with ties broken
by lower timesteps then path. `held-out-episodes.json`, `held-out-table.txt`
and `held-out-report.json` contain the frozen comparison; `replay-*-*` files
hold a standalone reload's results. Per-episode JSON records `split`,
`checkpoint`, `training_timesteps`, `policy`, `game_seed`, `outcome`, `length`
(learner decisions), and `return`. Tables count wins/losses/core draws and
cutoffs separately, report rates over all games, score (win 1, draw 0.5,
loss/cutoff 0), mean/median decisions, mean return and paired differences.
Held-out paired 95% intervals resample whole game seeds 10,000 times with
`random.Random(0)`; a positive lower endpoint against random, hold and
center-then-hold is required to support improvement. Cutoffs remain core
`in_progress`, neither a loss nor a draw. A selected checkpoint may be
audited using the existing inspector after `load_checkpoint`:
`inspect_trained_episode(model, seed, step_limit)`.

The fixed experiment at seed 0, step limit 50, 512 requested/collected
timesteps, rollout 64, batch 32, interval 4, evaluated both 256- and
512-timestep snapshots on all 200 validation seeds; their scores tied at
0.708, so 256 was selected. Its held-out score on 200 distinct seeds was
0.677 (95% score interval [0.620, 0.733]); validation's score interval was
[0.650, 0.763]. Held-out paired differences were +0.230 vs random
([0.143, 0.315]), +0.128 vs hold ([0.053, 0.203]) and -0.087 vs
center-then-hold ([-0.160, -0.018]). The overall result is **worse** against
the predeclared tactical baseline. This small fixed scenario and random
opponent do not establish broader skill. The local artifacts for this run are
in `/tmp/opencode/ppo-04-evidence`; use the commands above to create durable
artifacts at a location of your choice.

## Local core-game inference

Run a bounded, ordinary core `Game` with a frozen manifest-selected checkpoint
(or pass `--checkpoint checkpoint-000000256.zip` for an explicit manifest
entry when selection has not yet happened):

```sh
export PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m battle_agent_rl.ppo.local_game /tmp/opencode/ppo-04-evidence --seed 42
```

From Python, construct
`PPOPlayer.from_checkpoint("Learner", [Faction("learner", "Learner", "blue")],
run_dir, checkpoint=None, step_limit=None)`, put it first in the fixed 5×5
game against `SeededRandomPlayer`, then call `player.bind_game(game)` before
its first turn. The default checkpoint is the frozen manifest `selected` entry;
if none exists, give the path of an entry listed in `checkpoints`. An optional
`step_limit` must match the manifest. Loading validates versions, policy
contract, digest and spaces on CPU. The player refuses other board/settings/
unit/opponent configurations and repeated same-turn calls. Its callbacks do
not learn, advance turns or classify results. Use a fresh player for each game.

The local command prints each decision's occupancy, defensive-fire readiness,
remaining steps, legal mask indexes and chosen destination. It uses the same
`random.Random(seed)` for the opponent, defensive fire and combat as training,
resolves each returned movement plan and combat through core, and reports
`completed` versus `cutoff` separately; a cutoff leaves core in progress.
Core `GamePlayer.play(max_turns=...)` has a different turn bound and RNG
protocol and cannot substitute for this demonstration. On the existing
256-timestep selected checkpoint, seeds 0, 2 and 42 yielded 17, 4 and 9
decisions, all completed as learner wins; each decision's observation, mask
and action and the resulting fire/combat logs matched a fresh Gym checkpoint
evaluation replay with the same seed. This verifies integration, not skill.

## Evidence and observation audit

Uniform random play over seeds 0–99 won 36, lost 44 and drew 20 games (mean
4.92 steps). The inspector verifies each observation and legal mask against
core, including after combat and at endings. For this fixed task:

| Decision factor | Policy access |
| --- | --- |
| Positions and eliminated units | Occupancy. |
| Defensive-fire eligibility | Readiness plane; includes opponent off-turn fire risk. |
| Legal movement and hold | Core-derived mask; every legal destination has a path. |
| Remaining time to cutoff | `remaining_steps`, added by the 02 audit. |
| Unit attributes, terrain and fire settings | Fixed by the scenario. |
| Movement/retreat history | Current readiness and positions capture its next-decision effects; new turns refresh movement. |
| Turn/status/event history | Diagnostic `info`, not policy input. |
| Future opponent choices and rolls | Private seeded randomness. |

No mask change was needed. A cutoff remains distinguishable from a completed
game even when its core status is `in_progress`. For reproducibility, two
seed-12 CPU runs (Python 3.12.3, Torch 2.5.1+cpu, NumPy 2.5.4, Gymnasium
1.2.3, SB3/SB3-Contrib 2.7.0, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`, limit 2,
32 timesteps, n_steps 16, batch size 8, [16, 16] network) matched action and
outcome traces and timesteps; parameters and update metrics agreed within
`rtol=1e-6, atol=1e-7`. Results need not match across hardware or versions.

## Multi-unit prototype

Increment 06 provides a separate fixed 9×9, one- or two-unit-per-side
environment. It is **not** a replacement for the 5×5 trainer, its checkpoints,
or `PPOPlayer`. Learner decisions choose a slot and row-major destination:
`action = slot * 81 + row * 9 + column` (162 actions). Core resolves movement
and defensive fire immediately; once every living unit has received one order,
core resolves combat and runs the opponent's complete turn. At a decision, the
mask contains only the pending slots' reachable cells. `MultiUnitEnvironment`
supports `reset(seed)` and `step(action)`; `MaskedMultiUnitEnv` exposes a Gym
`Dict` observation and native `action_masks()` to `MaskablePPO`'s
`MultiInputPolicy`. No training campaign or multi-unit checkpoint/player is
included. For inference with a compatible initialized model, use
`multi_unit_gym.predict_joint_action(model, observation, mask)`; it checks
the model spaces before masked prediction. The contract identifier is
`battle-hexes-9x9-2slot-unit-destination-live-v1`.

From the repository root, inspect bounded deterministic play without trainer
dependencies (the Python 3.12 environment may be activated first):

```sh
export PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src
python -m battle_agent_rl.ppo.multi_unit_inspection --seed 17 --cycle-limit 2 --policy random
python -m battle_agent_rl.ppo.multi_unit_inspection --seed 3 --cycle-limit 1 --policy hold --learner-count 1 --opponent-count 2
```

The inspector prints slot positions and mutable fire/movement inputs, legal
indexes, selected orders, core events and the ending; it audits each state
against core and fails on inconsistencies. `cycle_limit` is a count of complete
two-sided turns, not learner orders. At most twice that many learner decisions
occur; a cutoff remains `in_progress` in core. Slots retain identity across
elimination; dead and absent units have zero-valued inputs except `present`
for dead units. This design demonstrates legal timing and stable inputs, not
policy strength or compatibility with the core `Player.movement()` batch
contract. Increment 07 now has bounded masked-PPO smoke training, a versioned
checkpoint and frozen core/API/UI plumbing, but its durable-browser acceptance
gate remains unverified. Report measured outcomes without a strength threshold; do
not grow this into a 9×9 skill campaign or assume its weights or policy-input
contract transfer to Crossroads. The experimental 9×9 opponent is to be hidden
or retired when the evaluated Crossroads player is delivered in 12; useful
internal 9×9 verification can remain. See the
[active schedule](../specs/ppo-agent/playable-player-schedule.md).

## Experimental trained 9×9 game (increment 07 in progress)

Two trained v3 checkpoints are Git-managed at
`battle_agent_rl/archive/ppo/x86_64/` and `battle_agent_rl/archive/ppo/arm64/`.
Each directory holds only `manifest.json` and `checkpoint.zip`. There are no
versioned run folders; the manifest still records the policy contract and
runtime versions so mismatched weights cannot be used. To explicitly replace
one model, from the repository root run:

```sh
source .venv312/bin/activate
./battle_agent_rl/train-ppo.sh          # host architecture, native Python
./battle_agent_rl/train-ppo.sh arm64    # optional: ARM64 on x86 via Docker/QEMU
./battle_hexes_api/dev.sh              # serves the matching local architecture
```

The launcher defaults to the host architecture; pass `x86_64` or `arm64` to
target one explicitly. On x86, ARM64 training builds a training-only image with
the same pins as deployment, then runs it locally; it does not train at deploy
time. On ARM64 hardware it trains in the active native Python environment,
which must match the pinned serving runtime. Install `requirements.txt` and
`requirements-ppo.txt` for native development. The training command clears
only the selected architecture's old generated files before invoking the
bounded trainer; it refuses unexpected files. Commit both the new manifest and
checkpoint together. Evaluation output is ignored by Git, not a third model.
The API Docker image independently serves the committed ARM64 model, while
`dev.sh` serves the committed model matching the host (unless explicitly
overridden). A local Python environment with different recorded versions must
retrain its architecture before serving; checks are not relaxed.

In another terminal run `npm run build && npm run serve` in `battle-hexes-web`
and open `http://localhost:4173` to select **Elimination Demo 3**. PPO occupies
the first seat; Human, Random or Q-Learning may play second.

### Bundled ARM64 image (deployment verification)

The API image bundles `battle_agent_rl/archive/ppo/arm64/` at a fixed path and
validates its manifest and checkpoint during build; it never trains during
build, startup or deployment. Python 3.12.3 and the exact ARM64 runtime pins
are in the Dockerfile and
[`requirements-ppo-serving.txt`](../requirements-ppo-serving.txt). For the
build, HTTP smoke check and resource limits, see the
[API README](../battle_hexes_api/README.md#arm64-release-image-deployment-verification).
PyTorch ARM64 `2.5.1` and x86 `2.5.1+cpu` have different recorded versions.
The Git-tracked x86 model was trained with seed 0, 16 legal timesteps and 20
optimizer steps; its checkpoint SHA-256 is
`b85abc07d44898cb576a3a1cce2290623685b40e1fd80be6924d4e68fb467cd7`.
On seeds 1000–1019 it produced 0 wins, 0 losses, 20 draws and 0 cutoffs.

The bundled seed-0 run requested and collected 16 timesteps (rollout 16,
batch 8), all 16 sampled actions were legal, one episode completed in a draw,
and 20 minibatch optimizer steps across 10 PPO epochs changed the policy
parameters. Its archive is 384 KiB, SHA-256
`242ea5aba62c3a1df33dcf0a494fe2fc8579a2aa8bb44c68dccd8ced11472091`.
The manifest records Python 3.12.3, NumPy 2.5.4, PyTorch 2.5.1,
Gymnasium 1.2.3, Stable-Baselines3 2.7.0 and SB3-Contrib 2.7.0; the
Dockerfile's Python base and `requirements-ppo-serving.txt` are the
installation sources for these exact versions. Training and serving use the
same pinned ARM64 runtime. These are connectivity checks, not a skill measurement.
Fresh-process deterministic replay on the declared seeds 1000–1019 produced
1 win (seed 1004), 0 losses, 19 draws and 0 cutoffs; all 20 core games
completed. The per-seed report from this verification is in
`/tmp/opencode/ppo-arch-arm-evaluation.json` outside the tracked model. New
commits of either architecture's model should be evaluated again before
deployment.
The released ARM64 image validated the artifact at build time and served, over
HTTP with no external artifact setting, PPO creation, one masked order and GET,
plus ordinary game creation, movement and GET. Under `--cpus 0.25 --memory
512m` on x86/QEMU it started in 47 seconds; startup memory was 101.1 MiB,
post-inference steady memory 431.6 MiB and cgroup peak 465,440,768 bytes
(about 444 MiB). The existing ECS 512 MiB limit passed this bounded single-
client, in-memory check, so no resource change was made. This is not a load
test or the durable browser acceptance demonstration; deployment with DynamoDB
and concurrent games may need separate measurement.

Elimination Demo 3 has a 10-turn core limit and defensive-fire sound mappings
for both factions. The checkpoint is specific to this scenario, not arbitrary
boards or rosters. The server validates its manifest, digest, scenario,
spaces and versions before creating a PPO game; clients never choose a model
path. Retraining either architecture replaces its tracked model and **expires
saved games bound to its previous digest**. GET or order returns a specific
checkpoint-unavailable error, with an explanation in server logs and the
browser; it never silently swaps in the new weights. Start a new game after
retraining. The default in-memory API store does not survive process restart;
configure DynamoDB for durable games. The browser resumes a pending order from
`GET /games/{id}` while its checkpoint is still current. Increment 07 remains
open until the durable backend-connected browser playthrough is verified.

## Direction

Keep training and inference on the same observation, mask and action-to-plan
mapping, with core authoritative for movement, combat and victory. The
center-then-hold comparison challenges the current policy's strength; revisit
training/representation before claiming improvement. Frozen 5×5 inference uses
the core `Player` interface; the 9×9 v3 slice uses live per-unit inference,
while Crossroads still needs its own contract. Follow the
[active schedule](../specs/ppo-agent/playable-player-schedule.md) for the bounded
path from the 07 human-visible 9×9 vertical slice to a trained, evaluated
Crossroads opponent on a declared side. Schedule 2's final playable target is
Crossroads, not the experimental prototype; its campaign extends 07's training
and checkpoint plumbing under a separate contract. The ultimate goal is
demonstrated Crossroads playing strength;
[schedule 3](../specs/ppo-agent/crossroads-strength-schedule.md) is an inactive
placeholder to be defined after the active schedule is fully implemented.
