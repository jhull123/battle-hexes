# Defensive Fire Web Sound Effects Specification

## Purpose

This document defines frontend behavior for defensive-fire sound playback using
faction-authored sound mappings, while keeping UI classes (such as `Menu`)
focused on presentation concerns.

## Scope

This spec covers:

- where faction sound data comes from in the web app state,
- how defensive-fire sounds are selected and played,
- class responsibilities between `Menu`, `Game`/`Faction`, and `SoundPlayer`,
- error tolerance and expected silent behavior for missing configuration.

This spec does **not** define audio settings UI, mixing policy beyond sequential
event handling, or non-defensive-fire sound domains.

## Data source and model contract (important)

### `GET /scenarios` is metadata-only

The scenario list endpoint is intentionally sparse (id/name/description/victory
metadata). It must **not** be treated as a source of faction sound mappings.

### Faction sounds must live in game state

Faction sound mappings must be available on the loaded game state and carried
into frontend domain models:

- `Game` owns the scenario/faction sound data used during gameplay.
- Each `Faction` instance should represent its own `sounds` mapping.
- Defensive-fire sound resolution must read from the firing unit's `Faction`
  model (or data already materialized from it), not from `Menu`-fetched
  scenario metadata.

## Faction sound configuration contract

Each faction may define defensive-fire sounds at:

- `faction.sounds.defensive_fire.effect`
- `faction.sounds.defensive_fire.no_effect`

Values are filenames under `battle-hexes-web/public/sounds`.

Runtime asset path:

- `/sounds/<filename>`

Example faction:

```json
{
  "id": "german",
  "name": "German",
  "sounds": {
    "defensive_fire": {
      "effect": "k98_rifle.ogg",
      "no_effect": "k98_distant.ogg"
    }
  }
}
```

## Required playback behavior

1. **Outcome mapping**
   - Use `defensive_fire_events[].outcome` from movement responses.
   - If `outcome === "no_effect"`, use `no_effect`.
   - Otherwise, use `effect`.

2. **Faction mapping**
   - Determine firing faction from `firing_unit_id` by resolving the firing unit
     in current game state.
   - Play the firing faction's configured sound key exactly once per event.

3. **Missing config**
   - If the sound key is missing/empty, play nothing.
   - Do not throw.
   - Do not fallback to defaults or other factions.

4. **Load/play failures**
   - If file loading or playback fails, gameplay and UI updates continue.
   - Log warning to console only.

5. **Multiple events**
   - Play per-event sounds as events are processed in sequence with animation.

## Class responsibility split

### `Menu`

- Displays defensive-fire messages/status in the UI.
- Delegates sound effects to `SoundPlayer`.
- Must not contain faction-resolution or sound-selection logic.

### `SoundPlayer`

- Owns game sound orchestration logic.
- Provides reusable faction sound lookup support (generic nested key-path
  retrieval, not hard-coded to defensive fire only).
- Implements defensive-fire playback as first concrete use case.
- Handles playback errors internally with warnings.

### `Game` / `Faction`

- `Game` supplies authoritative, runtime scenario/faction data.
- `Faction` exposes sound mappings so `SoundPlayer` can resolve per-faction
  sounds without relying on `/scenarios` metadata responses.

## Testing requirements

Frontend tests should cover at minimum:

1. Effect outcome playback from firing faction mapping.
2. No-effect outcome playback from firing faction mapping.
3. Missing config (missing section/key/empty filename) produces silence.
4. Faction-specific selection with multiple factions.
5. Playback failure tolerance (warning + no gameplay/UI interruption).
6. `Menu` delegates to `SoundPlayer` rather than implementing audio logic.
7. Faction sounds are resolved from gameplay state models (`Game`/`Faction`),
   not scenario-list metadata.

