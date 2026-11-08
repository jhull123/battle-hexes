# 08b — Executable non-learning environment

**08b is implemented and verified; increment 08 remains incomplete.**
AC-001–AC-004 run through production `ScenarioEnvironment.reset/step`.
Gym/policy/trainer/artifact integration and the human driver remain **08c**;
training campaigns remain **09**. No Crossroads weights, serving player or
strength claim is delivered.

## Delivered boundary

- `scenario_environment` orchestrates a `ScenarioTask` with an explicit learner
  seat. Scenario facts, full rosters, slots, masks, observations and action
  conversion remain data-driven. Both learner seats and an unregistered 5×7
  editor JSON with two arrival groups run to core completion without Python
  registration or scenario-specific engine code.
- `live_turn` extracts 07's live order/phase sequence. The 07 boolean-pending
  adapter keeps its original conversion, unscored behavior and artifacts; the
  new environment opts into core's ordinary scoring points. Core alone resolves
  movement, fire/retreat, combat, deployment, scores and completion. The encoder
  remains read-only. No mechanics were copied into the environment.
- Pending IDs are consumed for hold, retreat and elimination. Every active
  return is a legal learner movement decision; empty turns close through core
  without an invented pass. One game RNG drives core and sorted-joint-index
  opponent choices; random learner inspection uses a separate seeded RNG.
- `decision_controller`, `decision_audit` and `scenario_inspection` separate
  non-learning selection, live-state audits and JSON-line presentation from turn
  orchestration. Production modules are below 250 lines; no large-method/module
  exception is needed. No Gymnasium/Torch/SB3 import is needed for inspection.

## Acceptance evidence

| Gate | Production-path coverage |
| --- | --- |
| AC-001 | Reset plays all six opening Airborne orders before Wehrmacht, counts zero learner orders and retains `[8]`; reset also aggregates controlled opening fire/combat. Fresh fixed-shape arrays fit the task space and track core positions, stacks, casualties, movement, public fire flags, scores and arrivals. |
| AC-002 | Either German slot can go first; Feldwache only holds. Hold/fire retreat/elimination consume IDs. Invalid scalar/index/mask/route/partial-budget requests preserve serialized game, pending, counters, logs and RNG. Fire is spent before the next decision; applicable combat resolves once per side, not per unit. Empty German reset turns and empty Airborne turns advance without prediction; opening movement completion and later opponent combat completion stop immediately. |
| AC-003 | Unblocked groups arrive on the wrap into turn 3, before Airborne. Controlled live Airborne movement/combat cannot receive fire from fresh arrivals and kills either both arrivals or MG alone before the first learner order. Surviving StuG keeps slot 4, full core movement and public readiness. Capacity-blocked arrivals retry only on later wraps, not handoffs. Empty Germans with eligible arrivals are not fabricated elimination wins. |
| AC-004 | Hold/random games complete on turn 8 with objective results. Controlled two-objective Airborne occupation gives learner loss/−1; empty objectives give Wehrmacht win/+1; a different loaded scenario draws/0. Post-combat loss of the scoring occupant changes the final score before evaluation. Scores revert on vacating an objective, rather than accumulating. Nonterminal elimination rewards zero. A two-cycle cap stops before Airborne turn 3, retaining core's arrival state and `[6]`; completion on a bound takes precedence, with cleared ending masks/pending and rejected subsequent steps. |

Committed regressions: `test_scenario_environment.py`, `test_scenario_arrivals.py`,
`test_scenario_endings.py`, `test_scenario_scoring.py` and
`test_scenario_inspection.py` under `battle_agent_rl/tests/ppo/`.
Controlled state/RNG fixtures intentionally encounter edge cases; seed-only
rollouts are not used as proof of blocked arrivals, casualties or losses.

## Exact inspection commands

From the repository root:

```sh
source .venv312/bin/activate
export PYTHONPATH="$PWD/battle_agent_rl/src:$PWD/battle_hexes_core/src"
python -m battle_agent_rl.ppo.scenario_inspection --scenario d_day_crossroads --learner-seat 1 --seed 0 --policy hold --opponent-policy hold --expect-ending completed
python -m battle_agent_rl.ppo.scenario_inspection --scenario d_day_crossroads --learner-seat 1 --seed 17 --policy random --expect-ending completed
python -m battle_agent_rl.ppo.scenario_inspection --scenario d_day_crossroads --learner-seat 1 --seed 0 --policy hold --opponent-policy hold --cycle-limit 2 --expect-ending cutoff
./server-side-checks.sh
```

All three inspection invocations were run twice on Python **3.12.16**, NumPy
**2.5.4**; each pair compares byte-for-byte equal. Traces record loaded data's
SHA-256, identity/version, interface, slot order, core player order, seeds,
controllers/cap, runtime versions, legal decisions, orders/paths, intervening
core events and authoritative endings. `--policy-seed` defaults to the game
seed; `--scenario-dir` accepts editor JSON without a registry.

| Trace | Learner orders | Ending | Scores (learner/opponent) | Reward / remaining |
| --- | ---: | --- | --- | --- |
| seed 0 hold/hold | 36 | completed, turn 8, `objective_control` | 3 / 0 | +1 / `[1]` |
| seed 17 random/random | 36 | completed, turn 8, `objective_control` | 3 / 0 | +1 / `[1]` |
| seed 0 hold/hold, cap 2 | 6 | cutoff, core `in_progress`, turn 3 | 3 / 0 | 0 / `[6]` |

Every trace includes the two-unit arrival at `(0,16)` on turn 3. The cutoff
trace includes no Airborne turn-3 action despite the arrival. The random trace
includes one core combat event. Hold's opening opponent actions are
`227,547,934,1261,1584,1915`; its learner actions are `69,401,765` for cycles 1–2
then `69,401,765,988,1312` for cycles 3–8. Random's opening actions are
`1876,565,879,1247,245,1550`; first six learner orders are
`385,85,765,125,371,765`. Full action/event traces are generated by the commands,
not committed model artifacts.

Trace SHA-256, in the table's order:

```text
7ceb7f11549b62833d9a6a2b842f14093504f3716ae117440b44713b37d103cf
bc0a926285e82c9d5886dcb418a70041d41ed7baaf88fa69cf07275bf919a83f
321676fdd6e51caccfddd20466fe07cb60e34886a2603c024e9e07b7be019155
```

The prescribed Python 3.12 server checks pass: **213 core, 231 RL and 224 API
tests passed**, including existing 5×5/06/07 and API live-order/persistence tests.
All **38 new environment/inspection checks** pass. Both legacy inspection
smokes, Flake8, Ruff and the Pylint module-size gate pass. The AnyIO pytest plugin
emits its existing pytest deprecation warning; 11 DynamoDB integration tests
are skipped.
No 06/07 checkpoint, manifest, contract, scenario or public player choice changed.

## Remaining limitations

This is a fixed-roster, two-player, finite-horizon non-learning environment,
not policy compatibility across scenarios or multi-scenario training. Loaded
tasks can derive different spaces/action mappings. No human-command driver,
Gym wrapper, initialized Crossroads policy, trainer task selector, artifact
compatibility integration or campaign is claimed; AC-005–AC-006 remain open.
