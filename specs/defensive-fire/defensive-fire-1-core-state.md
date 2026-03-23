# Defensive Fire Core State Specification

## Purpose

This document defines the **core state-model and turn-timing changes** required to implement defensive fire eligibility correctly in `battle_hexes_core`.

This spec is intentionally limited to:

- representing defensive-fire eligibility explicitly,
- computing eligibility at the right time,
- resetting off-turn usage state at the right time, and
- recording retreat history needed to revoke or deny eligibility.

It does **not** define movement-time reaction resolution, API payloads, or frontend behavior. Those are covered by separate defensive-fire specs.

## Rulebook requirements covered by this spec

This spec covers the following requirements from `HOW_TO_PLAY.md`:

- A unit may use defensive fire at most once per off turn.
- A unit is eligible only if, on its previous turn, it ended the turn with **more than one movement point remaining** and it **was not forced to retreat**.
- Units whose printed movement is `0` are still eligible even though they never end a turn with more than one movement point remaining.
- Defensive fire eligibility is computed at the end of the unit's friendly turn.
- A unit loses defensive-fire eligibility immediately if it is forced to retreat before it fires.
- Defensive fire usage state resets at the start of a player's turn.

## Current state of the code base

The repository already contains a `defensive_fire_available` boolean on `Unit`, but it currently overloads multiple meanings:

- eligible to defensive fire this off-turn,
- already spent defensive fire this off-turn,
- not eligible because the prior turn ended incorrectly,
- no longer eligible because the unit was forced to retreat.

`Game.next_player()` currently restores defensive fire for units owned by the player whose turn just ended. That matches the existing UI expectation but not the rulebook's timing rules.

`Game.apply_movement_plans()` also toggles defensive fire for the moving unit during movement, which is a heuristic and should not remain the source of truth for eligibility.

## Design goals

1. **Rule fidelity first**
   - Eligibility and reset timing should match `HOW_TO_PLAY.md` exactly.
2. **Minimal ambiguity in state**
   - Core code should be able to distinguish eligibility, expenditure, and retreat-based disqualification directly.
3. **Preserve API/UI compatibility**
   - `defensive_fire_available` may remain as a derived/public-facing convenience flag if that simplifies compatibility.

## Required core state model

## 1. Add explicit defensive-fire state to units

Add unit state that captures the last completed friendly-turn outcome and the current off-turn usage state.

A preferred representation is:

- `ended_last_friendly_turn_with_defensive_fire_eligibility: bool`
- `forced_to_retreat_since_last_friendly_turn: bool`
- `defensive_fire_spent_this_off_turn: bool`

A smaller equivalent model is acceptable if it remains explicit and easy to reason about.

The implementation should avoid relying on indirect inference where a direct flag would be clearer.

## 2. Keep `defensive_fire_available` as a derived/public answer

The existing boolean may remain in API output and frontend models, but core logic should no longer treat it as the sole source of truth.

The core model should expose a derived/public answer equivalent to:

- is this unit currently able to defensive fire?

That answer should be based on:

- ownership relative to the current player,
- end-of-last-friendly-turn eligibility snapshot,
- whether the shot has already been spent this off-turn,
- whether the unit has been forced to retreat since the snapshot was recorded.

## 3. Compute eligibility at end of friendly turn

At the point where a player's turn is finalized, compute each of that player's units' eligibility for the upcoming enemy turn.

For each unit owned by the outgoing player:

1. Determine whether the unit was forced to retreat at any point during its just-completed turn.
2. Determine how many movement points it has remaining.
3. Mark the unit eligible for the upcoming enemy off-turn if:
   - `move == 0`, or
   - `moves_remaining > 1`,
   and the unit was **not** forced to retreat.
4. Persist that eligibility snapshot.
5. Reset `defensive_fire_spent_this_off_turn` to `False` so the unit may react during the upcoming enemy turn.

## 4. Reset usage state at the start of a player's turn

The rulebook says defensive fire status resets **at the start of a player's turn**.

Required behavior:

- when a player's new turn begins, that player's units should clear any "spent this off-turn" state,
- those units should begin their active turn normally,
- the game must still retain enough information to compute eligibility for the next enemy off-turn when the turn ends.

Implementation should normalize around this timing model:

- **start of player A's turn**: reset player A's defensive-fire usage state,
- **end of player A's turn**: compute whether each player A unit is eligible for the enemy off-turn.

## 5. Record forced-retreat history

Whenever a unit is displaced by a mandatory retreat effect, core rules must mark that unit as having been forced to retreat since its last eligibility snapshot.

At minimum, this includes:

- retreat caused by standard combat resolution,
- retreat caused by defensive fire,
- retreat caused by any future reaction or special rule.

This flag is used in two ways:

- when computing end-of-turn eligibility for the next enemy turn,
- when revoking currently displayed defensive-fire availability immediately if the unit retreats before firing.

## Explicitly out of scope for this spec

This spec does **not** include:

- resolving defensive fire during movement,
- defensive-fire probability calculations,
- defensive-fire event payloads in the API,
- frontend display of defensive-fire events.

## Concrete code areas expected to change

## `battle_hexes_core`

### Unit model

- Add explicit state for eligibility basis, forced-retreat disqualification, and once-per-off-turn expenditure.
- Keep or replace `has_defensive_fire()` with a derived/public method that answers current availability.

### Game / turn flow

- Move eligibility computation to end-of-turn logic.
- Reset usage state at the correct start-of-turn moment.
- Stop relying on the current boolean toggle as the authoritative rule.

### Combat / retreat support

- Ensure any forced retreat marks the unit appropriately for future defensive-fire eligibility calculation.

## Tests required

Add or update tests covering:

- end-of-turn eligibility for `moves_remaining > 1`,
- end-of-turn ineligibility for `moves_remaining == 1`,
- zero-move units remaining eligible by exception,
- forced retreat during the turn making a unit ineligible,
- start-of-turn reset semantics,
- immediate revocation when a unit is forced to retreat before firing.

## Definition of done

This spec is complete only when all of the following are true:

- defensive-fire eligibility is computed from end-of-turn state rather than opportunistic movement toggles,
- zero-move units are handled correctly,
- retreat history is recorded explicitly enough to deny or revoke eligibility,
- each unit can be identified as eligible, spent, or disqualified without ambiguity,
- the existing availability indicator can still be derived for API/frontend use.
