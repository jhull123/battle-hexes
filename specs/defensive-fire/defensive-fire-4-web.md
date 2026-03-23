# Defensive Fire Web Frontend Specification

## Purpose

This document defines the **frontend integration changes** required for defensive fire in `battle-hexes-web`.

This spec is intentionally limited to:

- preserving the existing defensive-fire indicator icon,
- consuming backend-authored defensive-fire event payloads during movement resolution,
- updating frontend synchronization, messaging, and animation hooks.

It assumes the core and API defensive-fire specs have already been implemented.

## Design goals

1. **Backend remains authoritative**
   - The frontend should display backend results rather than deciding whether defensive fire occurred.
2. **Preserve the existing availability indicator**
   - Units should continue to show the icon whenever `defensive_fire_available` is true.
3. **Surface reaction events clearly**
   - Defensive fire should be visible to players during movement resolution, in the movement phase itself.

## Current state of the code base

The frontend already stores `defensiveFireAvailable`, resets it at turn changes, and draws an indicator icon when available.

That gives the UI an existing presentation hook for defensive-fire availability.

However, the frontend currently has no concept of a backend-authored defensive-fire event and no dedicated logic for movement being interrupted mid-resolution by a defensive-fire retreat.

## Required behavior

## 1. Keep the existing availability indicator behavior

Continue displaying the defensive-fire indicator icon whenever the backend says `defensive_fire_available` is true.

The frontend should treat that field as authoritative and should not attempt to infer availability from local movement heuristics.

## 2. Consume defensive-fire event payloads as part of movement resolution

Defensive fire happens immediately during movement resolution when an enemy unit becomes adjacent, not as a separate later phase. After a move is submitted and the server responds, the frontend must treat any defensive-fire payloads as part of that same movement resolution and must:

- update unit positions,
- update defensive-fire availability flags,
- consume any defensive-fire event list returned by the API,
- surface the result to the player.

Expected visible outcomes include at least:

- defensive fire occurred and caused retreat,
- defensive fire occurred and had no effect.

## 3. Support movement interruption or revision during the movement phase

If movement is animated client-side before server confirmation, the frontend must allow defensive-fire reactions to occur during that movement presentation and to:

- interrupt the in-progress movement presentation,
- revise the mover's final displayed position,
- update any follow-on UI state affected by the reaction result.

## 4. Do not calculate defensive-fire odds or outcomes locally

The frontend must **not** attempt to compute:

- whether a unit should defensive fire,
- defensive-fire probability,
- retreat vs no-effect outcomes.

Those decisions belong to the backend.

## Suggested UI integration points

Implementation may include:

- extending board/game synchronization logic to ingest `defensive_fire_events`,
- adding a message or event-bus hook for reaction-fire notifications,
- integrating defensive-fire outcomes into movement-phase animation control flow,
- updating tests around board updates and movement result handling.

The exact presentation can evolve later, but the first implementation should visibly communicate that defensive fire occurred.

## Explicitly out of scope for this spec

This spec does **not** include:

- client-side defensive-fire rules calculation,
- detailed probability UI,
- sound or particle effects,
- end-to-end animation polish beyond basic correctness.

## Concrete code areas expected to change

## `battle-hexes-web`

### Models and synchronization

- Keep `defensiveFireAvailable` support intact.
- Update board/game synchronization to handle defensive-fire events returned by the API.
- Ensure board state reflects authoritative post-reaction positions.

### UI / messaging / animation hooks

- Surface defensive-fire results to the player.
- Allow movement visualization to be interrupted or corrected when the server reports defensive-fire retreat.

## Tests required

Add or update tests covering:

- the icon still reflecting backend `defensive_fire_available`,
- movement-response handling updating positions when defensive fire resolves during movement,
- defensive-fire event payloads being consumed correctly,
- any new messaging or animation hooks used to present reaction results.

## Definition of done

This spec is complete only when all of the following are true:

- the existing defensive-fire indicator still reflects backend state,
- frontend synchronization handles backend-authored defensive-fire events,
- retreat/no-effect results are surfaced visibly to the player during movement resolution,
- the frontend does not recalculate defensive-fire rules or odds locally.
