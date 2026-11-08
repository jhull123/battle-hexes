# 08 partial delivery: data-driven state and action audit

Historical **08a** audit. The subsequent non-learning turn driver and its
AC-001–AC-004 validation are recorded in
[08b execution evidence](08-executable-environment.md); 08c remains open.

This is **not** increment-08 completion evidence. No environment rollout,
initialized-policy acceptance, training campaign or Crossroads artifact is
claimed. The [08 contract](../08-crossroads-environment-policy-contract.md)
remains authoritative; its turn/adapter/integration acceptance gates are open.

## Delivered boundary

**Scenario data plus runtime learner selection; shared decision machinery.**
`scenario_task.ScenarioTask(scenario_data, learner_seat)` accepts core-loaded
`ScenarioData`; `ScenarioTask.load(scenario_id, learner_seat=...,
scenario_dir=...)` loads JSON through core. No registration, named Python task
definition or scenario-name conditional is needed. A scenario editor can add a
new JSON file within the representation limits below. The learner seat is a
required runtime/training choice, not a per-scenario constant; the interface
version belongs to shared code. Scenario identity/version come from loaded data.
Core-created identities supply complete rosters/ownership, and core-resolved
configuration supplies dimensions, objectives, groups, horizon and bounds.

`task.bind_game(game, learner=None)` checks representation/interface compatibility,
not equality with reference gameplay. It checks dimensions/horizon, complete
roster/owners, objective coordinates, group IDs and observation bounds. Numeric
validation catches unsupported dtypes/ranges before encoding; objective control
requires core's unambiguous scoring-side rule. Changes to fire settings, terrain,
roads and unit stats within the configured interface are not rejected merely
because they differ from current Crossroads.
`decision_binding` retains identities through board history and all configured
groups; learner/opponent roles come from the configured seat, and the objective
scoring player is resolved separately from core's scoring-side metadata.

Shared `decision_contract` constructs spaces from dimensions and bounds;
`decision_observation` encodes those slots, cells, objectives, groups and horizon;
`decision_actions` owns pending masks and conversion using the existing shared
core-path validator. None hard-code Crossroads IDs, five/eleven slots, 18×18,
one group or eight turns. `task.observation_space()` / `task.action_space()`
declare spaces from the same derived spec. The Crossroads forwarding modules
and `scenario_binding` are removed, not replaced by new forwarding modules.
Slots are learner-first, lexicographically sorted by ID within each side's
complete scenario roster, including undeployed reserves. JSON/board insertion
order does not define slots. Arrivals and casualties never shift them.

The earlier interface extraction introduced `battle-hexes-unit-destination-live-v2`, replacing
the fixed eight-turn Crossroads v1 label. The checked-in scenario retains all
eleven identities, thirteen field schemas/bounds, slot order and 1,620 indices;
this does not claim compatibility across changed definitions. Adding/renaming
units can change slots/actions for a new episode, and changed dimensions or
bounds can change spaces. Model reuse requires concrete interface checks, not
just a matching version label. This refactor retains the existing v2 label;
it does not introduce another contract change. No Crossroads weights exist or
are migrated.

`task.create_game(rng)` returns a binding over raw core state; for Crossroads it
leaves Airborne active and scores uninitialized, as core
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
  battle_agent_rl/tests/ppo/test_scenario_task.py \
  battle_agent_rl/tests/ppo/test_multi_unit.py \
  battle_agent_rl/tests/ppo/test_playable_slice.py -q
./server-side-checks.sh
```

Focused checks: **123 passed** (57 Crossroads checks, 14 data-driven reuse checks,
29 scenario-interface checks and 23 existing 06/07 regressions). The same 118
pre-existing checks passed before the refactor. Exact-gameplay
rejection tests were replaced with variation/interface checks, not retained as
obsolete constraints. An explicit concrete-space assertion pins
all Crossroads field shapes, dtypes and bounds in addition to live-state values.

The reuse fixture has a **5×7 board, four units, two learner slots,
four-turn horizon and stacking limit 1**. It exercises both learner seats and
both scoring-side assignments, non-board objective order, derived bounds,
core default terrain, road metadata, core-reachable action mapping, caller-owned
pending and invalid-action non-mutation. Two reinforcement groups exercise
independent scheduled/delayed/entered status, immobile arrival holds, casualties
and stable identity when entered groups disappear from core's pending menu.
A zero-group/zero-objective variant checks empty arrays. These probe the decision
contract, not playable environments or trained-policy support.

An actual Crossroads-definition variation goes through `ScenarioTask`,
`create_game`, `bind_game`, spaces and shared observation/mask/plan machinery:
**19×20, 12 units (7 learner / 5 opponent), two groups, four objectives and an
11-turn horizon**, changed ownership, unit stats, terrain, road costs, scoring
side, fire settings and arrival schedule. Its bounds and spaces derive without
editing task constants. Score bounds follow core's objective count, not summed
point values; weighted and zero-point objectives are audited against core scoring.
Other checks cover stacked objective sums and arrivals
later than the scenario horizon, reserve IDs that sort before deployed units,
reordered declarations, stable post-arrival/post-casualty rebinding and empty
objective/group arrays. Unsupported cases fail clearly: missing/invalid horizon,
invalid dimensions/seat, orphan/duplicate units, unknown owners or empty roles,
unsupported objective rules, negative/nonfinite stats and `int8`/`int32` or
`float32` overflow. Live interface-compatible gameplay variations bind without
a reference-game comparison.

The end-to-end editor test writes **`editor-created-river-map.json`** into a
temporary directory: a differently named 5×7 scenario with four units, two
reserve groups, a four-turn horizon, changed stats/bounds and scoring metadata.
Four cases cover both learner seats and both directly supplied core-loaded data
and `ScenarioTask.load(id, scenario_dir=...)`. They exercise raw creation,
binding, exact core-reachability masks, every legal action's plan, non-mutating
conversion/errors, caller-owned hold consumption, arrivals and post-casualty
rebinding without slot shifts. Input snapshot isolation is checked separately.
No Python registration or scenario-specific production data is involved.

### Before/after Crossroads parity

A temporary probe captured the pre-refactor entry point and the new
`ScenarioTask.load("d_day_crossroads", learner_seat=1)` path with seed 17.
It serialized all thirteen arrays (values, shapes and dtypes), all space types/
bounds, ordered slot IDs, full masks and **every legal action's complete core
path** at five states: raw creation, opening Airborne hold, controlled defensive
fire/retreat with a spent learner order, turn-3 arrival stacks, and an arrival
casualty with stale pending IDs. The controlled retreat used action 59 and
fire roll 0.0, matching the retained live-fire regression.
The before/after JSON files compare byte-for-byte equal; both SHA-256 values are
`409314e79fcd8c96945a8d9d178e4d5e4afd2b1b9feb37938c7db54c4028d4de`.
The retained concrete-space/value/path and lifecycle tests are the committed
regression coverage; this probe is change evidence, not an exact-gameplay gate
in production.

Prescribed `./server-side-checks.sh` passes on Python 3.12.16: **213 core,
193 RL and 224 API tests passed; 11 API integration tests skipped**. Both
legacy rollout smoke commands, Flake8, Ruff and the Pylint module-size check
pass. The dependency's AnyIO pytest plugin emits a pytest deprecation warning.
No 06/07 contracts, checkpoints/manifests or public player choices are changed.

## Remaining scope

Turn execution/orchestration, automatic empty turns, opponent controllers and
human driver, terminal rewards/cutoffs, episode inspection/replay, thin Gym
adapter, initialized-policy checks, and trainer/artifact scenario selection
and validation remain future work. Training/evaluation campaigns remain 09.
The shared layer is a fixed-roster, public-state, two-player decision contract
with explicit finite horizon and bounds—not an arbitrary-scenario environment,
universal observation schema or multi-scenario trainer. Different loaded rosters,
boards or bounds can produce incompatible spaces/actions; loading them does not
authorize checkpoint reuse or demonstrate policy generalization. No trained
Crossroads policy exists. Increment 08 remains incomplete.
