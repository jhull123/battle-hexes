# Defensive Fire Implementation Specification

## Purpose

This document describes the changes required to implement **defensive fire** according to the rules in `HOW_TO_PLAY.md`, while taking into account the current state of the code base.

The intent is to turn the existing `defensive_fire_available` flag and UI indicator into a complete game mechanic that:

- preserves the eligibility rule from the rulebook,
- triggers automatically when an enemy moves adjacent,
- resolves either **forced retreat** or **no effect**, and
- keeps the backend, API payloads, and frontend presentation in sync.

## Rulebook requirements

`HOW_TO_PLAY.md` now defines defensive fire as follows:

- An off-turn unit fires automatically when an enemy unit moves into an adjacent hex.
- A unit may use defensive fire at most once per off turn, and the shot is consumed whether the result is retreat or no effect.
- A unit is eligible only if, on its previous turn, it ended the turn with **more than one movement point remaining** and it **was not forced to retreat**.
- Units whose printed movement is `0` are still eligible even though they never end a turn with more than one movement point remaining.
- Defensive fire eligibility is computed at the end of the unit's friendly turn.
- A unit loses defensive-fire eligibility immediately if it is forced to retreat before it fires.
- Defensive fire usage state resets at the start of a player's turn.
- The only possible results are:
  - the moving/offensive unit retreats one hex, or
  - no effect.
- If multiple eligible units occupy the same hex, each unit resolves defensive fire separately.
- When a unit becomes adjacent, its movement points are set to zero and then defensive fire is resolved.
- Effectiveness is probabilistic and scenario-driven:
  - `chance = base_probability × unit_modifier × terrain_modifier`
  - the final chance is clamped between scenario minimum and maximum values.

## Current state of the code base

The repository already contains partial defensive-fire support, but it is limited to availability tracking and display.

### What already exists

1. **Core unit state**
   - `Unit` contains a single boolean `defensive_fire_available`, defaulting to `True`.
   - There is no distinction between:
     - being eligible this off-turn,
     - having already spent defensive fire this off-turn,
     - being permanently ineligible because the prior turn ended incorrectly, or
     - losing eligibility because the unit was forced to retreat. 

2. **Turn transition logic**
   - `Game.next_player()` currently resets defensive fire to `True` for every unit owned by the player whose turn just ended.
   - This matches the existing UI expectation, but it does **not** enforce the rulebook condition that eligibility depends on how that unit ended its own previous turn.

3. **Movement logic**
   - `Game.apply_movement_plans()` disables defensive fire for the moving unit when it spends all but one move point or when it ends adjacent to an enemy.
   - This is a proxy for the eligibility rule, but it is incomplete:
     - it does not explicitly store how many movement points remained at end of turn,
     - it does not handle forced retreat as a disqualifier,
     - it does not trigger any off-turn reaction shot,
     - it only updates the **moving** unit, not the defending unit that should react.

4. **API serialization**
   - API schemas serialize `defensive_fire_available` in full and sparse unit payloads.
   - This is enough to preserve the current indicator, but not enough to explain why a unit is or is not eligible, whether it has already fired this off-turn, or what defensive-fire result occurred.

5. **Frontend model and rendering**
   - The web model stores `defensiveFireAvailable`, resets it at turn changes, and draws an indicator icon when available.
   - The frontend therefore already has the right presentation hook for "this unit can defensive fire," but it has no concept of resolving a defensive-fire event.

### Summary of the gap

The code base currently treats defensive fire as a **single availability flag**. The rulebook describes it as a **turn-spanning reaction mechanic** with:

- eligibility determined by the prior turn's ending state,
- automatic triggering during enemy movement,
- once-per-off-turn consumption,
- interaction with retreat resolution, and
- outcome logic influenced by unit/terrain data.

Implementation should therefore be treated as a rules-engine feature, not only a UI toggle.

## Design goals

1. **Rule fidelity first**
   - Eligibility and reset timing should match `HOW_TO_PLAY.md` exactly.

2. **Backend is authoritative**
   - Defensive fire should be resolved in the core/game layer and exposed through API responses.
   - The frontend should display backend results rather than independently deciding whether a defensive-fire event occurs.

3. **Minimal ambiguity in state**
   - Replace the overloaded boolean-only mental model with explicit state that answers:
     - was this unit eligible at the start of the off-turn?
     - has it already spent its shot this off-turn?
     - was it disqualified because of forced retreat?

4. **Extensible resolution model**
   - The initial implementation can support only `retreat` or `no_effect`, but the design should leave room for richer combat-result reporting and animation.

## Proposed design

## 1. Track defensive fire eligibility as derived game state

The existing boolean can remain as the API/UI-facing convenience flag, but core logic should be driven by more explicit state.

### Proposed unit-level state additions

Add unit state that captures the last completed turn outcome for that unit, for example:

- `ended_last_friendly_turn_with_defensive_fire_eligibility: bool`
- `forced_to_retreat_since_last_friendly_turn: bool`
- `defensive_fire_spent_this_off_turn: bool`

An acceptable alternative is a smaller state model, such as:

- `last_turn_moves_remaining: int | None`
- `last_turn_forced_retreat: bool`
- `defensive_fire_available: bool`

However, the implementation should avoid relying on indirect inference when a direct flag would be clearer.

### Eligibility rule

At the start of an enemy off-turn, a unit should be considered able to defensive fire if all of the following are true:

- the unit belongs to the non-current player,
- it has not already spent defensive fire during this off-turn,
- it was marked eligible at the end of its own previous friendly turn, and
- it has not been forced to retreat since that eligibility snapshot was computed.

That end-of-turn eligibility snapshot should itself be computed from:

- whether the unit was forced to retreat during its just-completed friendly turn, and
- either:
  - its printed movement is `0`, or
  - it ended its own previous turn with **more than one** movement point remaining.

### Why this change is needed

The current implementation only clears the boolean during movement and restores it on turn handoff. That is not enough to distinguish:

- a unit that ended with 2+ movement points,
- a unit that ended with 1 point,
- a unit that ended adjacent and had to stop,
- a unit that was later forced to retreat by combat, and
- a zero-move unit that is always eligible by exception.

## 2. Reset defensive fire at the correct time

The rulebook says defensive fire status is reset **at the start of a player's turn**.

### Required behavior

When a new player turn begins:

- all units belonging to the **current player** should clear any "spent this off-turn" status,
- those same units should begin their own active turn normally,
- units that were previously eligible should remain visibly eligible only until they fire or are forced to retreat, and
- the system should preserve enough information to determine eligibility for the *next* enemy off-turn when that player's turn ends.

### Important clarification

The existing logic resets the previous player's units when the turn advances. That gives a similar visible result, but the implementation spec should normalize around the rulebook wording:

- **start of player A's turn**: reset player A's defensive-fire usage state,
- **end of player A's turn / transition to enemy off-turn**: compute whether each player A unit is eligible to react during the enemy turn.

This design makes turn timing easier to reason about and better matches future event logging.

## 3. Determine eligibility when the active player finishes movement/combat

A unit's defensive-fire availability for the upcoming enemy turn should be computed from the ending state of its own turn, not opportunistically toggled during every move.

### Proposed end-of-turn calculation

At the point where a player's turn is finalized:

For each unit owned by that player:

1. Determine whether the unit was forced to retreat at any point during its just-completed turn.
2. Determine how many movement points it has remaining.
3. Mark it eligible for the upcoming enemy off-turn if:
   - `move == 0`, or
   - `moves_remaining > 1`,
   and it was **not** forced to retreat.
4. Persist that eligibility snapshot so the off-turn state can be revoked immediately if the unit retreats before firing.
5. Reset `defensive_fire_spent_this_off_turn` to `False` so it may react during the enemy turn.

### Consequence

This removes the need for the current heuristic "set defensive fire unavailable as soon as the moving unit reaches one movement point or enemy adjacency" as the source of truth. That heuristic may still be useful for UI hints during the active turn, but it should not be the authoritative rule.

## 4. Trigger defensive fire automatically during movement resolution

Defensive fire happens when an enemy unit **moves into combat position (becomes adjacent)**.

### Trigger condition

During movement step resolution, after the moving unit enters each hex:

1. Apply the normal movement-stop rule as soon as the mover becomes adjacent by setting its remaining movement points to zero.
2. Identify enemy units adjacent to the mover's new hex.
3. Filter that set to units with defensive fire currently available.
4. For each eligible defending unit, check whether the adjacency is newly created by this move step.
   - Defensive fire should only trigger when the mover **becomes adjacent**, not when it starts adjacent and remains adjacent.
   - Because movement halts on first adjacency, the mover will not simultaneously become newly adjacent to one enemy while remaining free to continue moving around another.
5. Resolve the defensive fire event immediately after movement halts and before any further action is taken with that mover.

### Why step-by-step resolution matters

Movement is path-based. A unit may become adjacent midway through a path, and defensive fire can force retreat before the path completes. Therefore defensive fire cannot be implemented correctly as only an end-of-path check.

### Ordering recommendation

If multiple eligible defenders occupy the same adjacent hex at the triggering step, each of them should resolve defensive fire separately:

- resolve them in a deterministic order,
- stop further reactions if the moving unit has already been retreated/eliminated/otherwise removed from the triggering hex,
- record every attempted or resolved reaction event for API/UI use.

A simple deterministic order is ascending unit id, or board order if that is already stable.

## 5. Resolve defensive fire outcomes in the core combat/rules layer

The initial mechanic has only two outcomes:

- `retreat_one_hex`
- `no_effect`

### Proposed resolution API

Introduce a core-level result object such as `DefensiveFireResult` or `ReactionFireResult` with fields like:

- `firing_unit_id`
- `target_unit_id`
- `trigger_hex` / `target_hex_before`
- `outcome` (`retreat`, `no_effect`)
- `retreat_destination` (if any)
- `spent_defensive_fire` (`true` when the shot is consumed)
- optional debug or odds metadata for future UI display

### Resolution responsibilities

The resolver should:

1. Evaluate whether the defending unit is still eligible.
2. Calculate the final defensive-fire chance from scenario, unit, and terrain data:
   - read `base_probability`, `minimum`, and `maximum` from the scenario's `defensive_fire` settings,
   - multiply by the firing unit's `defensive_fire_modifier` (default `1.0`),
   - multiply by the target hex terrain's `defensive_fire_modifier` (default `1.0`),
   - clamp the result between the scenario minimum and maximum.
3. Roll against that final probability.
4. If the result is retreat:
   - force the moving unit to retreat using the existing combat retreat logic,
   - reuse the same retreat direction and blocked-retreat rules already enforced for normal combat,
   - update board/unit state immediately.
5. Consume the defender's defensive fire for the off-turn regardless of result.
6. Return structured results for logging, API responses, and animation.

### Retreat handling

Defensive fire should use the existing combat retreat logic for both retreat direction and blocked-retreat handling.

The code base already has `Unit.forced_move(board, from_hex, distance)` for retreat-like movement. That should be evaluated as the starting point for defensive-fire retreat handling, but the implementation must ensure the helper is invoked in exactly the same way normal combat retreats are resolved so the two systems stay consistent.

## 6. Record forced-retreat history

Because the rulebook says a unit is not eligible if it "was forced to retreat," the game must record whether a unit was forced to retreat during its own previous turn.

### Required sources of forced retreat

At minimum, this includes:

- retreat caused by standard combat resolution,
- retreat caused by defensive fire,
- retreat caused by any future reaction or special rule.

### Proposed rule-engine behavior

Whenever a unit is displaced by a mandatory retreat effect, set a per-unit flag indicating that it was forced to retreat since its last defensive-fire eligibility snapshot was computed.

This flag is then used in two ways:

- when computing defensive-fire eligibility at the end of the unit's next friendly turn, and
- to revoke currently displayed defensive-fire availability immediately if the unit retreats before firing.

## 7. Keep the API indicator, but expand payloads for events

The existing `defensive_fire_available` property should remain, because the frontend already uses it for the counter icon.

### API changes needed

The API should continue to serialize the current availability flag on units, but also expose defensive-fire results when movement is submitted. Examples of useful additions:

- a list of defensive-fire events resolved during the submitted movement,
- updated sparse unit positions after any retreat,
- enough event metadata for the frontend to show messages or animations.

### Suggested response shape

A movement/combat response could include:

- updated board/unit state,
- `defensive_fire_events: []`,
- any resulting combat state recalculation,
- optional human-readable messages.

The exact schema can be chosen later, but the spec should require structured events, not only a silently changed board state.

## 8. Frontend changes

The frontend already draws the icon indicating availability. That should remain, but the UI flow must be updated to treat defensive fire as a server-authored reaction event.

### Required frontend behavior

1. Continue displaying the icon whenever `defensive_fire_available` is true.
2. After a move is submitted and the server responds:
   - update unit positions,
   - update defensive-fire availability flags,
   - surface any defensive-fire result to the player.
3. If movement is animated client-side before server confirmation, ensure defensive-fire reactions can interrupt or revise that animation.

### Important constraint

The frontend should **not** attempt to calculate defensive-fire outcome odds on its own. The backend should remain authoritative.

## Concrete code changes expected by area

## battle_hexes_core

### Game / turn flow

- Add explicit defensive-fire eligibility/spent-state handling to turn lifecycle.
- Compute upcoming off-turn eligibility from end-of-turn state.
- Stop relying on the current boolean toggle as the only source of truth.

### Movement resolution

- Resolve movement one step at a time.
- After each entered hex, detect newly adjacent enemy units with defensive fire.
- Interrupt movement when defensive fire causes retreat.
- Return structured defensive-fire results along with updated board state.

### Unit model

- Add state needed to represent:
  - previous-turn eligibility basis,
  - forced-retreat disqualification,
  - once-per-off-turn expenditure.
- Keep a derived/public method that answers whether the unit currently has defensive fire available.

### Combat / retreat support

- Reuse or extend forced-retreat utilities.
- Ensure any forced retreat marks the unit appropriately for future defensive-fire eligibility calculation.

### Tests to add/update

- end-of-turn eligibility calculation for:
  - `moves_remaining > 1`,
  - `moves_remaining == 1`,
  - `move == 0`,
  - forced retreat during the turn.
- automatic trigger when a unit becomes newly adjacent.
- no trigger when adjacency already existed before the step.
- once-per-off-turn consumption.
- multiple eligible defenders around one moved unit.
- retreat result updates board position correctly.
- no-effect result leaves position unchanged.
- turn reset semantics.

## battle_hexes_api

- Preserve `defensive_fire_available` in unit schemas.
- Add response/event schemas for defensive-fire outcomes.
- Ensure sparse board updates can reflect movement interrupted by reaction retreat.
- Add schema tests covering new event payloads and state propagation.

## battle-hexes-web

- Keep existing indicator icon behavior.
- Update board/game synchronization to handle defensive-fire events returned from the API.
- Add/adjust UI messaging or animation hooks for reaction results.
- Add tests ensuring the icon still reflects backend state and that event payloads are consumed correctly.

## Out of scope for the first implementation

To keep the first implementation tractable, the following should be explicitly out of scope unless clarified otherwise:

- manual player choice of whether to defensive fire,
- multiple outcome tables beyond `retreat` and `no_effect`,
- detailed probability UI,
- sound/particle effects,
- e2e animation polish.

## Implementation clarifications

The answers that were previously tracked as open questions are now part of the implementation requirements:

- Eligibility is computed at the end of the friendly turn, and the icon/availability must disappear immediately if the unit retreats or fires before using that eligibility.
- Each eligible unit in the same hex resolves defensive fire separately.
- Defensive fire is always consumed when it fires, regardless of result.
- Probability uses the scenario-driven formula documented in `HOW_TO_PLAY.md` and illustrated in `d_day_crossroads.json`.
- Retreat destination and blocked-retreat behavior both reuse the existing combat retreat logic.
- A unit cannot trigger new adjacency against one enemy while already continuing movement beside another, because movement halts when adjacency is created.
- Movement halts first, then defensive fire is resolved.
- The frontend should visibly show the results of defensive fire during movement resolution.
- Defensive fire is fully automatic, so no AI decision hook is required for the first implementation.

## Recommended implementation sequence

1. Refactor core unit/game state so eligibility is computed explicitly.
2. Add step-based movement interception and defensive-fire result objects.
3. Expose results through API schemas.
4. Update frontend synchronization/UI messaging while preserving the existing icon.
5. Add comprehensive tests across core, API, and web.

## Definition of done

Defensive fire implementation should be considered complete only when all of the following are true:

- the indicator icon reflects true rulebook eligibility,
- eligibility depends on prior-turn movement remainder and retreat history,
- zero-move units are handled correctly,
- defensive fire triggers automatically on newly created adjacency,
- each unit can fire at most once per off-turn,
- the only current outcomes are retreat or no effect,
- retreat/no-effect resolution is authoritative in the backend,
- API responses expose reaction results in a structured way,
- frontend state updates correctly after defensive-fire resolution,
- automated tests cover the major eligibility and resolution scenarios.
