# 08 partial delivery: Crossroads state and action audit

This is **not** increment-08 completion evidence. No environment rollout,
initialized-policy acceptance, training campaign or Crossroads artifact is
claimed. The [08 contract](../08-crossroads-environment-policy-contract.md)
remains authoritative; its turn/adapter/integration acceptance gates are open.

## Delivered boundary

The new `crossroads_*` modules under `battle_agent_rl.ppo` bind core-loaded
`d_day_crossroads` version `1` to Player 2 / Wehrmacht. A pinned, canonical
SHA-256 covers scenario gameplay (not presentation names, descriptions, colors
or sounds). Binding also compares live static rules, owner/faction assignments,
roster stats, terrain, roads, objectives and reinforcement declarations against
the approved core-built game. Unit/hex insertion order does not define slots.
Board history and reinforcement groups retain all eleven permanent identities.

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
  battle_agent_rl/tests/ppo/test_multi_unit.py \
  battle_agent_rl/tests/ppo/test_playable_slice.py -q
./server-side-checks.sh
```

Focused checks: **98 passed** (75 Crossroads checks plus 23 existing 06/07
regressions). Prescribed server-side checks pass on Python 3.12.16: **213 core,
168 RL and 224 API tests passed; 11 API integration tests skipped**. Both
legacy rollout smoke commands, Flake8, Ruff and the Pylint module-size check
pass. The dependency's AnyIO pytest plugin emits a pytest deprecation warning.
No 07 checkpoints/manifests or public player choices are changed.

## Remaining scope

Turn execution/orchestration, automatic empty turns, opponent controllers and
human driver, terminal rewards/cutoffs, episode inspection/replay, thin Gym
adapter, initialized-policy checks, and Crossroads trainer/artifact selection
and validation remain future work. Training/evaluation campaigns remain 09.
