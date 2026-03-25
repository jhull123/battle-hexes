# Defensive Fire API Specification

## Purpose

This document defines the **API-layer changes** required to expose defensive-fire state and movement-time defensive-fire events to clients.

This spec is intentionally limited to:

- preserving the existing unit availability indicator,
- exposing structured defensive-fire results in server responses,
- ensuring sparse and full payloads stay in sync with authoritative backend state.

It assumes the core-state and core-resolution defensive-fire specs have already been implemented in `battle_hexes_core`.

## Design goals

1. **Backend remains authoritative**
   - Clients must receive defensive-fire outcomes from the backend rather than recomputing them.
2. **Preserve existing compatibility where possible**
   - `defensive_fire_available` should remain on unit payloads.
3. **Expose structured reaction events**
   - API responses should describe what happened during movement, not only the resulting board positions.

## Current state of the code base

The API currently serializes `defensive_fire_available` in full and sparse unit payloads.

That is enough for the current icon, but not enough to expose:

- why a unit is or is not eligible,
- whether a unit has already spent its shot this off-turn,
- what defensive-fire event occurred during movement,
- whether movement was interrupted by reaction retreat.

The `/games/{game_id}/movement` endpoint currently returns the game model and movement plans, but no defensive-fire event list.

## Required behavior

## 1. Preserve `defensive_fire_available` on unit payloads

Full and sparse unit payloads should continue to expose the current availability flag because existing frontend code already uses it for the defensive-fire indicator icon.

This field should continue to reflect the backend-authoritative current answer for whether the unit can defensive fire now.

## 2. Add structured defensive-fire events to movement responses

When movement submission causes defensive fire to resolve, the API must expose those events in structured form.

Examples of useful response additions include:

- `defensive_fire_events: []`,
- updated board/unit state after any retreat,
- enough metadata for the frontend to show messages or animations,
- optional human-readable messages if helpful.

The exact schema may vary, but the payload must be structured enough that the frontend does not need to infer defensive-fire outcomes from silent board-state changes alone.

## 3. Keep sparse and full payloads synchronized

If defensive fire interrupts movement and forces retreat, the API should ensure that the returned board or sparse update reflects:

- the mover's final actual position,
- any changed `defensive_fire_available` flags,
- any units removed or displaced by mandatory retreat behavior,
- event data corresponding to the state transition.

## 4. Support future UI messaging without exposing game logic to the client

The API should provide enough defensive-fire result data for the frontend to:

- show that defensive fire occurred,
- identify the firing and target units,
- show retreat vs no-effect,
- update positions and status indicators.

However, the API should not require the frontend to calculate outcome odds or decide whether defensive fire should have occurred.

## Suggested response shape

A movement-related response may include:

- updated board/game state,
- `defensive_fire_events`,
- any other movement or combat recalculation data already returned by the endpoint,
- optional presentation-oriented messages.

The exact field names can be chosen during implementation, but the shape should remain stable and testable.

## Explicitly out of scope for this spec

This spec does **not** include:

- core rules for computing eligibility,
- movement-time defensive-fire resolution itself,
- frontend UI changes beyond the contract the frontend consumes.

## Concrete code areas expected to change

## `battle_hexes_api`

### Schemas

- Preserve `defensive_fire_available` in full and sparse unit schemas.
- Add response/event schemas for defensive-fire outcomes.
- Extend any movement-response schema or response assembly needed to carry defensive-fire event data.

### Endpoints

- Update movement-related endpoints to return defensive-fire results when movement resolves reactions.
- Ensure sparse board updates can reflect movement interrupted by defensive-fire retreat.

## Tests required

Add or update tests covering:

- serialization of `defensive_fire_available` after the core changes,
- movement responses including `defensive_fire_events`,
- sparse or full payloads reflecting retreat-induced position changes,
- propagation of defensive-fire event fields needed by the frontend.

## Definition of done

This spec is complete only when all of the following are true:

- existing unit payloads still expose `defensive_fire_available`,
- movement responses expose defensive-fire results in a structured way,
- payloads reflect authoritative post-reaction board state,
- the frontend has enough backend-supplied information to present defensive-fire results without recomputing rules locally.
