---
title: Game-State Codec
version: 1.0
date_created: 2026-09-19
last_updated: 2026-09-19
tags: [design, game-persistence, api, codec]
---

# Introduction

This specification defines increment 3.2 of the game-persistence schedule: an
API-owned codec that converts a complete authoritative core game to canonical
JSON bytes and reconstructs an independent game from those bytes and its
version-matched scenario.

## 1. Purpose & Scope

The increment defines persistence schema version 1, serialization, validation,
and hydration in `battle_hexes_api`. It covers every supported scenario and the
`human`, `random`, and `q-learning` player types. It does not implement a
repository, change routes, persist reinforcement definitions already present in
the scenario, or modify `battle_hexes_core`.

The intended implementer must treat [`docs/design.md`](../../docs/design.md),
especially sections 1.4, 1.5, 1.10, 1.12, and 1.17, as authoritative.

## 2. Definitions

| Term | Definition |
| --- | --- |
| Authoritative state | Runtime data required for subsequent game behavior or accurate history/status presentation. |
| Canonical JSON | UTF-8 JSON with sorted object keys, compact separators, unescaped Unicode, and no non-finite numbers. |
| Hydration | Rebuilding a detached core object graph from a scenario plus persisted dynamic state. |
| Stable reference | A scenario-defined ID or player name used instead of object identity in the document. |
| Scenario version | The string `ScenarioData.version` from the loaded scenario JSON. |

## 3. Requirements, Constraints & Guidelines

- **REQ-001**: Add `GameStateCodec` under
  `battle_hexes_api.persistence`. Its only public operations are those in
  section 4.1, and `STATE_SCHEMA_VERSION` is the integer `1`.
- **REQ-002**: Encoding must return canonical JSON bytes. It must reject an
  invalid or incomplete graph rather than omit data or stringify unknown
  objects.
- **REQ-003**: The version-1 document must contain exactly the top-level fields
  in section 4.2. Fields use `snake_case` because this is an internal
  persistence format, not the camel-case HTTP contract.
- **REQ-004**: Persist game ID; scenario ID and version; ordered player type
  IDs and player names; ordered active unit IDs; current player; turn number;
  current phase; ordered pending combats; terminal flag; game status; scores;
  every scenario unit's runtime state; reinforcement state and history; and
  ordered combat and defensive-fire histories.
- **REQ-005**: Persist each unit's ID, disposition, coordinates, remaining
  movement points, and all five defensive-fire runtime values:
  `ended_last_friendly_turn_with_defensive_fire_eligibility`,
  `forced_to_retreat_since_last_friendly_turn`,
  `defensive_fire_spent_this_off_turn`, `defensive_fire_available`, and the
  `defensive_fire_modifier`. A unit disposition is `active`, `reinforcement`,
  or `eliminated`; only active units have coordinates.
- **REQ-006**: Preserve order for players, `active_unit_ids`, pending combat
  entries and their attacker/defender IDs, reinforcement groups and attempts,
  combat events, defensive-fire events, and participant/eliminated/retreated
  lists within events.
- **REQ-007**: Serialize histories losslessly using the fields of the core
  `CombatEvent`, nested combat snapshots, `DefensiveFireEvent`, nested unit
  snapshots, and `ReinforcementArrivalEvent` dataclasses. Do not serialize the
  grouped HTTP game-log projection.
- **REQ-008**: Hydration must first parse and fully validate the document,
  require schema version 1, load `ScenarioData` and `Scenario` by `scenario_id`,
  and require an exact string match with `scenario_version`. Missing scenarios,
  mismatches, unsupported schemas, malformed JSON, invalid field types, unknown
  IDs, duplicate IDs, impossible references, and inconsistent dispositions
  raise `SavedGameIncompatibleError` with a non-sensitive reason category.
- **REQ-009**: Hydration must rebuild the baseline graph through the existing
  API/core creation path, then restore dynamic state without invoking game-rule
  evaluation, reinforcement deployment, player callbacks, random resolution,
  or any other state transition after the baseline is built.
- **REQ-010**: The hydrated graph must reconnect every unit to the canonical
  scenario faction and owning player; the board, reinforcement deployer,
  defensive-fire resolver/recorder, and players must reference the same board;
  current player must reference an entry in `game.players`; reinforcement
  groups must reference the same unit objects used elsewhere.
- **REQ-011**: Restore the saved `GameStatus` value directly. Codec and schema
  code must not call `GameStatusEvaluator`. A terminal game has
  `current_player_name: null`, `current_phase: null`, no pending combats, and
  `terminal: true`; an in-progress game has a known current player, a supported
  phase, and `terminal: false`.
- **REQ-012**: Recreate `human`, `random`, and `q-learning` players through one
  API-owned player construction path. Unknown player type IDs are incompatible.
  Each recreated player's board reference must be repaired after baseline game
  creation when the player implementation holds one.
- **REQ-013**: For `q-learning`, persist only the type ID. Hydration reloads the
  configured baseline Q-table/settings exactly as new-game creation does. Never
  persist Q-table contents, hyperparameters, turn counters, last actions,
  learning/exploration flags, pickle bytes, or process random-generator state.
- **REQ-014**: Validate that document game/scenario metadata agrees with the
  enclosing `StoredGame` metadata supplied to decode. The codec does not read
  or change `gameVersion`, timestamps, expiry, or encoded-item budgets.
- **REQ-015**: Access to non-public core attributes needed for restoration must
  be confined to the codec's hydration adapter. Routes, schemas, repositories,
  and tests outside codec fixtures must not duplicate that coupling.
- **CON-001**: Do not change `battle_hexes_core`, scenario JSON, HTTP response
  models, or live route behavior in this increment.
- **CON-002**: Do not use pickle, `eval`, Python object serialization, or class
  names from the document. Parsing untrusted bytes must not execute code.
- **GUD-001**: Split document validation, event conversion, unit restoration,
  and graph reconnection into focused helpers; avoid one monolithic codec
  method.

## 4. Interfaces & Data Contracts

### 4.1 Codec interface

```python
class GameStateCodec:
    STATE_SCHEMA_VERSION = 1

    def encode(
        self, game: Game, *, scenario_version: str
    ) -> bytes: ...

    def decode(self, stored_game: StoredGame) -> Game: ...
```

`encode` obtains `game.id`, `game.scenario_id`, and
`game.player_type_ids` from the game created by the API and validates the
supplied scenario version against the scenario source. `decode` validates the
document against `StoredGame.game_id`, `state_schema_version`, `scenario_id`,
and `scenario_version`. Decoded games retain `scenario_id`, `scenario_version`,
and a copied `player_type_ids` list for later projections and re-encoding.

Scenario loading should be an injected callable or small gateway so tests can
deterministically model missing and changed scenarios.

### 4.2 Version-1 document

The following shape is normative. Every field is required; nullable values are
explicit JSON `null`. Event objects contain every same-named core dataclass
field and use arrays for tuples.

```json
{
  "state_schema_version": 1,
  "game_id": "<uuid-string>",
  "scenario_id": "d_day_crossroads",
  "scenario_version": "1",
  "players": [
    {"name": "Player 1", "type_id": "human"},
    {"name": "Player 2", "type_id": "random"}
  ],
  "current_player_name": "Player 1",
  "turn_number": 2,
  "current_phase": "combat",
  "pending_combats": [
    {"attacker_unit_ids": ["a1"], "defender_unit_ids": ["d1"]}
  ],
  "terminal": false,
  "game_status": {
    "state": "in_progress",
    "winner_player_name": null,
    "winner_faction_id": null,
    "reason": null,
    "message": null
  },
  "scores": [{"player_name": "Player 1", "points": 3}],
  "active_unit_ids": ["a1", "d1"],
  "units": [
    {
      "unit_id": "a1",
      "disposition": "active",
      "row": 2,
      "column": 4,
      "movement_points_remaining": 1,
      "ended_last_friendly_turn_with_defensive_fire_eligibility": true,
      "forced_to_retreat_since_last_friendly_turn": false,
      "defensive_fire_spent_this_off_turn": false,
      "defensive_fire_available": true,
      "defensive_fire_modifier": 1.0
    }
  ],
  "reinforcements": [
    {"group_id": "r1", "entered": false}
  ],
  "reinforcement_history": [],
  "combat_history": [],
  "defensive_fire_history": []
}
```

`scores` has exactly one entry per player in player order. `units` has exactly
one entry per scenario unit in scenario declaration order. Reinforcement group
IDs exactly match the scenario groups in scenario order. `active_unit_ids`
defines board dictionary/insertion order and contains precisely units whose
disposition is `active`; reinforcement units belong to one non-entered group;
eliminated units occur in neither location.

Allowed phases are `movement`, `combat`, and `end_turn`, plus `null` only for a
terminal game. Coordinates are either two in-bounds integers for active units
or both `null` otherwise. Pending combat IDs must be active, unique within each
side, and owned by the appropriate current/opposing players. Numeric values
must be finite and booleans must not pass integer validation.

## 5. Acceptance Criteria

- **AC-001**: Given any registered scenario and supported player-type
  combination, encoding, decoding, and re-encoding produces identical bytes.
- **AC-002**: A hydrated game is detached from its source, but all internal
  identity relationships in REQ-010 are preserved.
- **AC-003**: Round trips preserve observable movement legality and cost,
  pending combat resolution, defensive-fire availability/outcomes under fixed
  randomness, reinforcement deployment/blocked attempts, scoring, turn/phase
  advancement, and rejection of commands after completion.
- **AC-004**: Round trips preserve exact ordered histories, scores, unit state,
  pending combats, and already-computed status without calling a status
  evaluator during decode.
- **AC-005**: Every incompatibility listed by REQ-008 fails before a partially
  hydrated game is returned and is translated to `SavedGameIncompatibleError`.
- **AC-006**: Q-learning round trips restore a fresh configured baseline agent;
  serialized bytes contain none of the excluded fields in REQ-013.
- **AC-007**: Existing API/core behavior and scenario files remain unchanged.

## 6. Test Automation Strategy

- Add parameterized codec unit tests for every scenario file and each supported
  player type in every player position allowed by the scenario.
- Build representative snapshots after movement, pending and resolved combat,
  successful and blocked defensive fire, reinforcement arrival attempts,
  scoring changes, and terminal victory/draw states. Assert public behavior and
  authoritative fields, not only document equality or private helper calls.
- Inject deterministic scenario loading and combat/defensive-fire randomness.
  Mutate a decoded graph to prove it cannot affect the original.
- Add negative tests for every REQ-008 category, terminal/phase inconsistency,
  bad references/order sets, illegal coordinates, and non-finite numbers.
- Spy only on the public evaluator boundary to prove decode does not reevaluate
  status; do not assert private codec helper calls.
- Run `./server-side-checks.sh`. No new coverage percentage is required.

## 7. Rationale & Context

Reloading immutable scenario configuration keeps snapshots compact, while the
version check prevents dynamic state from being applied to an incompatible
definition. Explicit IDs and ordered arrays make identity and behavior stable
without unsafe object serialization. Restoring computed status and history
avoids replaying rules or random decisions during a read.

## 8. Dependencies & External Integrations

- **DEP-001**: Increment 3.1 supplies `StoredGame` and
  `SavedGameIncompatibleError`.
- **DEP-002**: The existing scenario loader supplies both `ScenarioData.version`
  and the core scenario used by game creation.
- **DEP-003**: Existing API player/game factories supply consistent baseline
  construction; implementation may consolidate them without changing behavior.
- **DEP-004**: Python standard-library JSON is sufficient; no storage service or
  new package is required.

## 9. Examples & Edge Cases

| Case | Required result |
| --- | --- |
| Scenario file is absent or its version changed | `SavedGameIncompatibleError`; no fallback |
| Eliminated unit | Present in `units`, null coordinates, absent from board and pending groups |
| Not-yet-entered reinforcement | Present in `units` and exactly one pending group, absent from board |
| Entered reinforcement | Group has `entered: true`; unit disposition and board order are restored |
| Completed game | Persisted status restored; no rules execute; further core mutation remains rejected |
| Q-learning game | Fresh baseline artifact loaded; learned request-local state is absent |

## 10. Validation Criteria

- The document and code define one supported schema version and reject all
  others.
- Canonical encoding is byte-stable and complete for all authoritative fields.
- Hydration validates metadata before returning a detached, correctly linked
  object graph.
- The test matrix in section 6 passes with no `battle_hexes_core` changes.
- The specification and implementation remain inside the API persistence
  boundary and do not activate persistence at runtime.

## 11. Related Specifications / Further Reading

- [Implementation schedule](implementation-schedule.md), increment 3.2.
- [Persistence contracts and command identity](architecture-persistence-contracts-command-identity.md), increment 3.1.
- [Application persistence design](../../docs/design.md), sections 1.4-1.17.

## Open Questions

No questions.
