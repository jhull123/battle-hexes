# Defensive Fire Web Sound Effects Specification

## Purpose

This document defines the frontend behavior for **defensive-fire sound playback** using scenario-authored faction sound mappings.

It extends defensive-fire frontend behavior by adding sound hooks for defensive-fire outcomes.

## Scope

This spec covers only:

- selecting defensive-fire sounds from the scenario JSON,
- playing the firing faction's configured sound for defensive-fire outcomes,
- handling missing configuration by playing no sound.

This spec does **not** define broader audio architecture changes outside defensive fire.

## Scenario configuration contract

Each faction may define defensive-fire sounds under:

- `factions[].sounds.defensive_fire.effect`
- `factions[].sounds.defensive_fire.no_effect`

Values map to files in:

- `battle-hexes-web/public/sounds`

Example shape:

```json
{
  "sounds": {
    "defensive_fire": {
      "effect": "m1_single_rifle_shot.ogg",
      "no_effect": "m1_single_rifle_shot.ogg"
    }
  }
}
```

## Required behavior

## 1. Successful defensive fire uses `effect` sound

When a defensive-fire event resolves with a successful outcome (an effect is applied), the frontend must:

- identify the **firing faction** for that defensive-fire event,
- read `factions[].sounds.defensive_fire.effect` for that faction from the loaded scenario,
- play that sound exactly once for the event if configured.

## 2. No-effect defensive fire uses `no_effect` sound

When a defensive-fire event resolves with a no-effect outcome, the frontend must:

- identify the **firing faction** for that defensive-fire event,
- read `factions[].sounds.defensive_fire.no_effect` for that faction from the loaded scenario,
- play that sound exactly once for the event if configured.

## 3. Missing sound configuration results in silence

If the required sound key is missing or empty for that faction/event outcome, the frontend must:

- not throw,
- not fall back to another faction,
- not substitute a default defensive-fire sound,
- continue processing gameplay normally,
- play no sound.

## 4. File lookup behavior

When a sound value is present, treat it as a filename relative to `public/sounds`.

Expected asset path at runtime:

- `/sounds/<filename>`

If a referenced file does not exist or fails to load, gameplay must continue without blocking movement resolution.

## Integration guidance

Implementation is expected to integrate with existing movement/defensive-fire event handling by:

- adding a defensive-fire sound selection helper that accepts:
  - event outcome (`effect` or `no_effect`),
  - firing faction id,
  - scenario data,
- routing playback through existing/standardized frontend audio utilities,
- invoking playback at the same point where defensive-fire outcomes are surfaced to the user.

## Testing requirements

Add/adjust frontend tests to cover at minimum:

1. **Effect outcome playback**
   - Given an `effect` defensive-fire event and configured faction sound, playback is requested for `/sounds/<effect-file>`.
2. **No-effect outcome playback**
   - Given a `no_effect` defensive-fire event and configured faction sound, playback is requested for `/sounds/<no-effect-file>`.
3. **Missing config**
   - Given missing `defensive_fire`, missing outcome key, or empty filename, no playback is requested.
4. **Faction-specific selection**
   - With different sound mappings per faction, the firing faction's mapping is used.
5. **Load/play failure tolerance**
   - If playback utility reports an error, defensive-fire resolution and UI updates still complete.

## Out of scope

This spec does not define:

- volume balancing,
- layered/multiple simultaneous defensive-fire mix rules,
- user audio settings UI,
- global fallback sound libraries,
- non-defensive-fire sound effect behavior.

## Open questions

The following decisions are needed before implementation details can be finalized:

1. **Outcome mapping source of truth**
   - Which exact event field/value in the defensive-fire payload distinguishes `effect` vs `no_effect`?
2. **Multiple events timing**
   - If multiple defensive-fire events resolve in one server response, should sounds:
     - play for every event,
     - be rate-limited,
     - or collapse to one sound per movement action?
3. **Concurrent playback policy**
   - If multiple sounds trigger close together, should they overlap, queue, or interrupt/replace?
4. **Missing file telemetry**
   - Should missing audio files be logged to console only, reported through app telemetry, or fully silent?
5. **User mute/settings behavior**
   - Should defensive-fire sounds obey an existing global mute/effects-volume setting, and if so, which control path is canonical?
6. **Future key naming stability**
   - Is `defensive_fire.effect` / `defensive_fire.no_effect` considered stable contract, or should implementation support aliases for backward compatibility?
