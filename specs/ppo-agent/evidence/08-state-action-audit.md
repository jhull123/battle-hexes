# 08 partial delivery: Crossroads state and action audit

This is **not** increment-08 completion evidence. No environment rollout,
initialized-policy acceptance, training campaign or Crossroads artifact is
claimed. The [08 contract](../08-crossroads-environment-policy-contract.md)
remains authoritative; its turn/adapter/integration acceptance gates are open.

## Delivered boundary

**Scenario-specific task definitions; scenario-independent decision machinery.**
`crossroads_scenario.TASK` is the small definition for core-loaded
`d_day_crossroads` version `1`, Player 2 / Wehrmacht: scenario identity, pinned
gameplay SHA-256, learner seat, ordered roster, bounds and concrete policy
contract. Crossroads is the first supported task for the reusable layer, not a
separate scenario-specific engine. Its observable contract has not changed.

Shared `scenario_binding` validates scenario gameplay (excluding presentation
names, descriptions, colors and sounds) and compares live static rules,
owner/faction assignments, roster stats, terrain, roads, objectives and
reinforcement declarations against an approved core-built game.
`decision_binding` retains identities through board history and all configured
groups; learner/opponent roles come from the configured seat, and the objective
scoring player is resolved separately from core's scoring-side metadata.

Shared `decision_contract` constructs spaces from dimensions and bounds;
`decision_observation` encodes those slots, cells, objectives, groups and horizon;
`decision_actions` owns pending masks and conversion using the existing shared
core-path validator. None hard-code Crossroads IDs, five/eleven slots, 18×18,
one group or eight turns. `crossroads_contract` is a concrete-space facade only.
Unit/hex insertion order does not define slots. Crossroads still retains all
eleven identities; its field schemas, slot order and 1,620 indices are unchanged.

Raw game creation leaves Airborne active and scores uninitialized, as core
creates them; it is not `reset()`. Tests initialize scoring and advance phases
explicitly through core. A future driver must score at ordinary core scoring
points, execute each order's live effects, consume its pending ID, and handle
turns, terminal rewards and cutoffs. Conversion itself is read-only.

## Input/mask audit

- All thirteen observation arrays match the specified shapes, dtypes and space
  bounds. They are fresh, unnormalized and learner-first without reordering core.
- After core closes an opening Airborne hold turn, German cells are 69, 77 and
  117; holds are actions 69, 401 and 765. Feldwache's only enabled action is 765.
  Reserved blocks 3–4 are false. Already-computed scores encode as `[3, 0]`.
- Separate rows retain friendly stacks. Removed units remain eliminated even
  with stale coordinates; awaiting units cannot become deployed by coordinates
  alone. Stats persist while off-board movement/fire/positions are zero.
- Public fire flags are read relative to Wehrmacht, including real core
  defensive-fire consumption and forced retreat. No readiness is reset/cached.
- Terrain includes resolved defaults. Road directions match core's actual
  column-parity offsets, retaining all six boundary directions. Declared roads
  expose edge costs only: a road into rough terrain still costs **2**, not 1.
- Objective control uses Airborne occupation in scenario order. Scores are
  read, never recomputed by encoding. Horizon is `max(0, 9 - turn_number)`;
  disabling inputs/masks at a cutoff does not zero the true horizon.
- Core wraps into turn 3 before Airborne acts, atomically stacking MG/StuG at
  `(0,16)` when permitted. They cannot fire during that intervening Airborne
  movement. German movement then exposes distinct holds 988/1312; a pre-order
  casualty stays eliminated in its reserved slot. Entered group status persists
  after casualties.
- One entry occupant blocks both arrivals. Handoffs do not retry; subsequent
  cycle wraps do. Group status follows core's pending menu: at the due turn a
  blocked group is still `scheduled`; on later turns it is `delayed` until entry.
- Masks exactly match core reachability, including stacking capacity and hold.
  Pending IDs, not remaining movement points, determine spent orders. Partial
  first-order budgets are rejected. Scalar integer validation, current mask,
  core endpoints, legal path steps and current budget are checked before mutation.
  Invalid inputs/routes preserve board/unit state, scores, pending orders,
  phase/turn, event histories and the seeded RNG state.

## Validation

With `.venv312` active and `PYTHONPATH=battle_agent_rl/src:battle_hexes_core/src`:

```sh
python -m pytest battle_agent_rl/tests/ppo/test_crossroads_*.py \
  battle_agent_rl/tests/ppo/test_decision_reuse.py \
  battle_agent_rl/tests/ppo/test_multi_unit.py \
  battle_agent_rl/tests/ppo/test_playable_slice.py -q
./server-side-checks.sh
```

Focused checks: **109 passed** (76 Crossroads checks, 10 internal reuse checks
and 23 existing 06/07 regressions). An explicit concrete-space assertion pins
all Crossroads field shapes, dtypes and bounds in addition to live-state values.

The internal reuse fixture has a **5×7 board, four units, two learner slots,
four-turn horizon and stacking limit 1**. It exercises both learner seats and
both scoring-side assignments, non-board objective order, configurable bounds,
core default terrain, road metadata, core-reachable action mapping, caller-owned
pending and invalid-action non-mutation. Two reinforcement groups exercise
independent scheduled/delayed/entered status, immobile arrival holds, casualties
and stable identity when entered groups disappear from core's pending menu.
A zero-group/zero-objective variant checks empty arrays. These are internal
configuration probes through the same implementations, not new task support.

Prescribed `./server-side-checks.sh` passes on Python 3.12.16: **213 core,
179 RL and 224 API tests passed; 11 API integration tests skipped**. Both
legacy rollout smoke commands, Flake8, Ruff and the Pylint module-size check
pass. The dependency's AnyIO pytest plugin emits a pytest deprecation warning.
No 06/07 contracts, checkpoints/manifests or public player choices are changed.

## Remaining scope

Turn execution/orchestration, automatic empty turns, opponent controllers and
human driver, terminal rewards/cutoffs, episode inspection/replay, thin Gym
adapter, initialized-policy checks, and Crossroads trainer/artifact selection
and validation remain future work. Training/evaluation campaigns remain 09.
The shared layer is a fixed-roster, public-state, two-player decision contract
with explicit finite horizon and bounds—not an arbitrary-scenario environment,
universal observation schema or multi-scenario trainer. Reusing this machinery
does not demonstrate policy generalization; no trained Crossroads policy exists.
