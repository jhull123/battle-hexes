# 08c — Policy integration evidence

Verified 2026-11-08 on Python 3.12.16, CPU. **08 is complete:** AC-001–AC-006
pass. This is integration evidence, not a training campaign or strength result.

## Reproduce

From the repository root (use fresh run directories if repeating):

```sh
source .venv312/bin/activate
export PYTHONPATH="$PWD/battle_agent_rl/src:$PWD/battle_hexes_core/src"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
python -m pytest battle_agent_rl/tests/ppo/test_scenario_gym_policy.py battle_agent_rl/tests/ppo/test_scenario_artifact.py battle_agent_rl/tests/ppo/test_scenario_human.py -q
python -m battle_agent_rl.ppo.multi_unit_train --scenario d_day_crossroads --learner-seat 1 --seed 23 --total-timesteps 16 --n-steps 16 --batch-size 8 --cycle-limit 2 --opponent-policy hold --run-dir /tmp/opencode/08c-crossroads-smoke
python -m battle_agent_rl.ppo.scenario_human --run-dir /tmp/opencode/08c-crossroads-smoke --scenario d_day_crossroads --learner-seat 1 --seed 1000 --scripted-human hold > /tmp/opencode/08c-human-1000.jsonl
python -m battle_agent_rl.ppo.scenario_human --run-dir /tmp/opencode/08c-crossroads-smoke --scenario d_day_crossroads --learner-seat 1 --seed 1000 --scripted-human hold > /tmp/opencode/08c-human-1000-repeat.jsonl
cmp /tmp/opencode/08c-human-1000.jsonl /tmp/opencode/08c-human-1000-repeat.jsonl
./server-side-checks.sh
```

Omit `--scripted-human hold` for interactive explicit orders. The driver prompts
for a human-local joint slot/destination index, re-prompts on invalid input and
aborts on EOF/interrupt; it never fills missing orders with holds. Add
`--cycle-limit 2` to the driver to replay the external-cutoff boundary.

## Configuration and results

- Loaded `d_day_crossroads`, scenario version `1`; runtime learner seat `1`
  (Wehrmacht), unchanged Airborne-first core order, true horizon 8. Shared
  interface `battle-hexes-unit-destination-live-v2`; 13 observation fields and
  `Discrete(1620)`, with unchanged permanent slot order.
- MaskablePPO `MultiInputPolicy`, default flatten/concatenate extractor and Tanh,
  separate `pi=[64,64]`, `vf=[64,64]`; one CPU environment/thread. Seed 23,
  rollout 16, batch 8, 10 epochs, learning rate 0.0003, gamma 0.99,
  GAE lambda 0.95, clip 0.2, entropy coefficient 0, value coefficient 0.5,
  maximum gradient norm 0.5, normalized advantages.
- Runtime: NumPy 2.5.4, Torch 2.5.1+cpu, Gymnasium 1.2.3,
  Stable-Baselines3/SB3-Contrib 2.7.0. Versions, configuration snapshot/digest,
  seed/configuration and checkpoint digest are recorded in the temporary manifest.
- Training: **16/16 legal masked steps, changed parameters, 20 optimizer updates,
  10 PPO epochs**; episode seeds `[23,24,25]`, two completed external cutoffs.
  Wall time about 5.5 seconds including interpreter/library startup.
- Temporary checkpoint SHA-256 for this run:
  `148ad9356848304297f9bf96610d11ac0ee2fe7ee2df9aca95628b3273d82e95`.
  This is not a committed/serving artifact; archive digests can vary on reruns.
- A second identical training invocation into
  `/tmp/opencode/08c-crossroads-smoke-repeat` produced bit-identical parameters
  and matching training metadata. Reloaded scripted-human replay matched the
  first trace exactly and left parameters unchanged. Automated reload tests also
  compare the original in-memory model's complete legal replay to its reloaded
  counterpart, including core events, scores and ending.
- Seed-1000 full replay: **36 legal learner orders**, arrivals on the wrap into
  turn 3 before Airborne acts, core objective-control completion on Wehrmacht's
  turn 8, scores `[3,0]`, learner reward `+1`. Two driver CLI traces matched
  byte-for-byte. Replay wall time about 5.2 seconds including startup.
- Opening human-local hold indices:
  `[227,547,934,1261,1584,1915]`. Learner indices by cycle:
  turns 1–2 `[35,415,765]`; turn 3 `[35,415,765,1399,1023]`;
  turns 4–8 `[35,415,765,1399,1002]`. Subsequent human orders are explicit
  holds in lowest-pending-slot order; full paths/events are in the JSON lines.
- The two-cycle driver replay requests no turn-3 human orders, retains normal
  core wrap/arrivals, core `in_progress`, horizon `[6]` and reward 0.

## Gates and regression coverage

| Gate | Verified observable behavior |
| --- | --- |
| AC-001–AC-004 | Retained `test_crossroads_*`, `test_decision_reuse`, `test_scenario_*` regressions: audited inputs/masks, non-mutation, live fire/retreat/casualties, automatic empty turns, blocked/attacked arrivals, scoring, completion and cutoff precedence. Non-learning inspection still rejects any import of Gym/trainer libraries. |
| AC-005 | Seed-23 initialized real MaskablePPO legally samples and deterministically predicts on reachable three-/five-unit and one-pending-unit states, plus the sole surviving Feldwache after two live fire eliminations. Hold-only mask contains exactly 765. Weights remain unchanged. Contract/draft, seat, slots, core order, spaces (including tiny bound changes), legacy 5×5/9×9 policies/artifacts, runtime and digest mismatches reject before prediction. Manifest and archive bindings are checked independently. |
| AC-006 | Explicit human callbacks run only in first-seat movement; PPO's first prediction follows all six opening human orders. A complete scripted-human game matches the substitute environment's orders, events, scoring, arrivals and ending. Invalid console input re-prompts; missing input aborts without PPO acting. Cutoff never requests next-cycle human input. |
| Data-driven boundary | Differently named editor JSON on a 5×7 board, two reinforcement groups and either learner seat trains and reloads through the same trainer/artifact path, without registration. Compatible gameplay changes within the representation are not rejected by an exact scenario fingerprint gate. |
| Gym boundary | Fresh native Boolean masks, declared arrays/spaces, reset seed sequence, terminal versus cutoff tuples, invalid-action non-mutation and ending masks are tested. A core ending during reset fails explicitly at the Gym boundary (reset has no termination flags), before a collector can predict on an empty mask. Structural inspection/human execution retain that ending. |

Focused integration tests: **34 passed**. Final `./server-side-checks.sh`:
**213 core, 265 RL, 224 API passed; 11 API integration skips**.
Flake8, Ruff and the 300-line production-module Pylint check passed. The only
test warning was the installed AnyIO plugin's upstream pytest deprecation.

Responsibilities remain separate: Gym tuple adaptation, task-interface metadata,
artifact persistence/validation, guarded inference, and local human input. Turn
orchestration stays in `ScenarioEnvironment`; all orders use `decision_actions`
and `live_turn` with core rules. New production modules are 40–113 lines; there
is no scenario-specific engine, registry, copied rule set or parallel trainer.
Existing 06/07 defaults, artifact checks and committed checkpoints are untouched.

No remaining increment-08 gate is open. Campaign training/evaluation, strength,
production artifacts, frozen evaluated-player parity, API/UI integration and
browser acceptance remain later increments and were not attempted here.
