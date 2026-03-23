# Defensive Fire Core Resolution Specification

## Purpose

This document defines the **movement-time defensive-fire rules engine** for `battle_hexes_core`.

This spec is intentionally limited to:

- stepwise movement interception,
- adjacency-trigger detection,
- defensive-fire resolution order and outcomes,
- retreat handling and result objects.

It assumes the unit-state and turn-lifecycle changes from `defensive-fire-1-core-state.md` are already in place.

## Rulebook requirements covered by this spec

This spec covers the following defensive-fire requirements from `HOW_TO_PLAY.md`:

- An off-turn unit fires automatically when an enemy unit moves into an adjacent hex.
- When a unit becomes adjacent, its movement points are set to zero and then defensive fire is resolved.
- A unit may use defensive fire at most once per off turn, and the shot is consumed whether the result is retreat or no effect.
- The only possible results are:
  - the moving/offensive unit retreats one hex, or
  - no effect.
- If multiple eligible units occupy the same hex, each unit resolves defensive fire separately.
- Effectiveness is probabilistic and scenario-driven:
  - `chance = base_probability × unit_modifier × terrain_modifier`
  - the final chance is clamped between scenario minimum and maximum values.

## Current state of the code base

`Game.apply_movement_plans()` currently computes movement cost across the path, moves the unit directly to the final hex, and only then updates a defensive-fire boolean for the mover.

That means the current implementation does **not**:

- resolve movement one step at a time,
- halt at the first hex where adjacency is created,
- trigger automatic off-turn reactions,
- interrupt movement when a retreat occurs,
- return structured defensive-fire results.

## Design goals

1. **Backend is authoritative**
   - Defensive fire must be resolved in the core rules engine.
2. **Correct movement timing**
   - Defensive fire must trigger during path resolution, not only at end-of-path.
3. **Deterministic and extensible results**
   - The first implementation supports only `retreat` and `no_effect`, but returns a structured result model suitable for API and UI use.

## Required movement-time behavior

## 1. Resolve movement one step at a time

Movement must be processed incrementally rather than by jumping directly to `plan.path[-1]`.

For each entered hex during path execution:

1. Apply the move to the entered hex.
2. Determine whether enemy adjacency was newly created by this step.
3. If adjacency was newly created:
   - stop movement immediately by setting remaining movement points to zero,
   - resolve defensive fire from eligible adjacent enemy units,
   - abort the rest of the planned path if retreat or any invalidating effect occurs.

This is necessary because a unit may become adjacent midway through a path, and defensive fire may force retreat before the path would otherwise complete.

## 2. Trigger only on newly created adjacency

Defensive fire should trigger only when the mover **becomes adjacent** because of the current step.

It should **not** trigger when:

- the mover started adjacent before the step,
- the mover remains adjacent but is not entering adjacency for the first time on this path,
- no new enemy adjacency was created by the entered hex.

Because movement halts on first adjacency, a unit should not continue moving while already adjacent in order to trigger new adjacency elsewhere.

## 3. Determine which units fire

After the movement-stop rule is applied for the triggering step:

1. Identify enemy units adjacent to the mover's new hex.
2. Filter that set to units whose defensive fire is currently available according to the core-state rules.
3. Resolve each eligible unit's defensive fire separately.

If multiple eligible defenders are present in the same hex, each unit still resolves separately.

## 4. Resolve in deterministic order

When multiple eligible defenders react to the same movement step, resolve them in deterministic order.

Acceptable ordering rules include:

- ascending unit id,
- stable board iteration order,
- another documented deterministic ordering already present in the codebase.

Further reactions should stop once the mover has already been retreated, eliminated, or otherwise removed from the triggering hex such that later reactions are no longer valid.

## Required resolution behavior

## 5. Introduce a structured defensive-fire result object

Add a core-level result object such as `DefensiveFireResult` or `ReactionFireResult`.

Recommended fields include:

- `firing_unit_id`
- `target_unit_id`
- `trigger_hex` / `target_hex_before`
- `outcome` (`retreat`, `no_effect`)
- `retreat_destination` (if any)
- `spent_defensive_fire`
- optional metadata for debugging or future UI display

The movement resolver should return structured defensive-fire results along with updated board state.

## 6. Calculate defensive-fire probability from scenario, unit, and terrain data

The resolver should compute the final chance as:

`chance = base_probability × unit_modifier × terrain_modifier`

Required inputs:

- `base_probability`, `minimum`, and `maximum` from the scenario's defensive-fire settings,
- firing unit's `defensive_fire_modifier` with default `1.0`,
- target hex terrain's `defensive_fire_modifier` with default `1.0`.

The final probability must be clamped between the scenario minimum and maximum.

## 7. Consume defensive fire regardless of outcome

Whenever a unit resolves defensive fire, the shot is spent for that off-turn regardless of whether the result is retreat or no effect.

## 8. Reuse existing retreat logic

If defensive fire succeeds, the moving unit retreats one hex.

Retreat handling must reuse the same retreat direction and blocked-retreat rules already enforced for standard combat.

The current code base already has `Unit.forced_move(board, from_hex, distance)` for retreat-like movement. The implementation should evaluate that helper as a starting point, but defensive fire must be wired so retreat resolution stays consistent with normal combat rules rather than creating a divergent retreat system.

## Explicitly out of scope for this spec

This spec does **not** include:

- defining the unit-state eligibility model,
- API serialization of defensive-fire events,
- frontend messaging or animation.

## Concrete code areas expected to change

## `battle_hexes_core`

### Game / movement resolution

- Resolve movement one step at a time.
- Halt movement on first newly created adjacency.
- Trigger defensive fire during movement resolution.
- Interrupt or terminate the remaining path when retreat occurs.
- Return structured defensive-fire results.

### Combat / retreat support

- Reuse or extract retreat helpers shared with standard combat.
- Ensure any mandatory retreat updates board state immediately and consistently.

### Scenario / probability support

- Read defensive-fire scenario settings and modifiers needed by the resolver.

## Tests required

Add or update tests covering:

- automatic trigger when a unit becomes newly adjacent,
- no trigger when adjacency already existed before the step,
- once-per-off-turn consumption,
- multiple eligible defenders around one moved unit,
- deterministic ordering when multiple defenders react,
- retreat result updating board position correctly,
- no-effect result leaving position unchanged,
- movement stopping on first adjacency before defensive fire is resolved.

## Definition of done

This spec is complete only when all of the following are true:

- movement is resolved incrementally enough to stop on first newly created adjacency,
- defensive fire triggers automatically at the correct moment,
- each eligible unit resolves at most once per off-turn,
- the only implemented outcomes are retreat or no effect,
- retreat behavior is consistent with standard combat retreat rules,
- core returns structured defensive-fire results suitable for downstream serialization.
