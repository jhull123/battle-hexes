---
title: Defensive Fire Game Log Events
version: 1.0
date_created: 2026-09-05
tags: [design, core, api, web, game-log, defensive-fire]
---

# Introduction

Extend the persisted Game Log with a record for every defensive-fire shot resolved during movement. Replace the existing transient defensive-fire text areas in the menu with that durable history while retaining defensive-fire sounds and unit availability indicators.

## 1. Purpose & Scope

This specification extends the turn/player Game Log contract in [Reinforcement Game Event Log](design-game-event-log.md) with `events.defensiveFire`.

It covers recording and displaying firing and target units, final success probability, random roll, and actual outcome. It does not change defensive-fire eligibility, probability calculation, shot ordering, movement interruption, retreat, elimination, sound effects, or unit indicators.

## 2. Definitions

- **Defensive-fire shot**: One defensive-fire resolution by an eligible defending unit against a moving target unit.
- **Firing unit**: The eligible enemy unit that resolves the shot.
- **Target unit**: The moving unit against which the shot resolves.
- **Success probability**: The final clamped probability used by the defensive-fire resolver to evaluate the shot.
- **Random roll**: The random value evaluated against the final success probability.
- **No effect**: The random roll did not cause a forced retreat.
- **Retreated**: The target successfully completed the forced retreat caused by the shot.
- **Eliminated**: The target was removed because it could not complete the forced retreat caused by the shot.

## 3. Requirements, Constraints & Guidelines

### Core history

- **REQ-001**: Core records one defensive-fire event for every actual defensive-fire shot resolved during movement, including no-effect shots.
- **REQ-002**: Record the firing and target units' stable IDs and display names, the final success probability, raw random roll, and actual outcome.
- **REQ-003**: Normalize the persisted outcome to exactly `noEffect`, `retreated`, or `eliminated`. A target removed after failing a forced retreat records `eliminated`, not `retreated`.
- **REQ-004**: A defensive-fire event belongs to the current moving player's turn/player game-log record, even though an opposing player owns the firing unit.
- **REQ-005**: Retain defensive-fire events in the same complete authoritative game history as reinforcement and combat events. They remain available after turn changes, game completion, game load, and browser refresh.
- **REQ-006**: Preserve the resolver's actual shot order when recording and serializing defensive-fire events for one turn/player record.
- **CON-001**: Do not record hypothetical eligible defenders that do not fire because the mover has already left the triggering hex.
- **CON-002**: This feature must not change defensive-fire probability calculation, random-number generation, resolution order, availability spending, movement, retreat, elimination, scoring, or game-status behavior.

### API contract

- **REQ-007**: Extend each existing `gameLog` record's `events` object with a `defensiveFire` array. It is empty when that turn/player record contains no defensive-fire shots.
- **REQ-008**: Return identical complete defensive-fire history to every player and agent. Do not filter firing units, target units, probabilities, rolls, or outcomes by viewer.
- **REQ-009**: Return the raw resolved probability and roll as numeric values. The frontend controls display rounding and must not recompute the outcome.
- **REQ-010**: Preserve the existing transient `defensiveFireEvents` movement-response field for sound playback and post-movement board updates in this phase. It is not the persistent history contract.
- **CON-003**: API schemas serialize recorded core history and must not recalculate defensive-fire eligibility, probability, rolls, or outcomes from current board state.
- **CON-004**: HTTP JSON uses camelCase. Python internals use snake_case.

### Web menu

- **REQ-011**: Render each defensive-fire event in the existing Game Log under the moving player's `Turn <turn> - <player name>` heading.
- **REQ-012**: Render a readable block titled `Defensive Fire` with labeled Firing unit, Target unit, Success probability, Random roll, and Result lines.
- **REQ-013**: Display the final probability as a percentage and the random roll rounded to exactly two decimal places. For example, raw `0.2841` displays as `28.41%` and `0.28`.
- **REQ-014**: Render player-readable result text for each normalized outcome: `No effect`, `Target retreated`, or `Target eliminated`.
- **REQ-015**: Render a concise player-readable summary that identifies the firing and target units and accurately describes the result.
- **REQ-016**: Remove the existing transient defensive-fire text from Game Stages and Selected Hex, including the `reactionMessages` and `reactionStatus` elements and their menu-controller behavior.
- **REQ-017**: Preserve defensive-fire sound playback and the board's defensive-fire availability icon/indicator behavior.
- **REQ-018**: Render the complete returned defensive-fire history on initial game load and whenever full game state replaces or updates client state.

## 4. Interfaces & Data Contracts

The existing `gameLog` turn/player record gains `events.defensiveFire`.

```json
{
  "turnNumber": 3,
  "playerName": "Player 2",
  "events": {
    "reinforcements": [],
    "combat": [],
    "defensiveFire": [
      {
        "firingUnit": {
          "unitId": "feldwache_a",
          "name": "Feldwache A"
        },
        "targetUnit": {
          "unitId": "rifle_platoon_b",
          "name": "Rifle Platoon B"
        },
        "successProbability": 0.2841,
        "randomRoll": 0.2317,
        "outcome": "retreated",
        "summary": "Feldwache A forced Rifle Platoon B to retreat."
      }
    ]
  }
}
```

- `events.defensiveFire` contains one entry per actual resolved shot for the record's moving player and turn.
- `firingUnit` and `targetUnit` retain both stable IDs and display names so the event remains understandable after either unit moves or is removed.
- `successProbability` and `randomRoll` are raw numeric values in the inclusive range `0.0` through `1.0` as resolved by core.
- `outcome` is exactly `noEffect`, `retreated`, or `eliminated`.
- `summary` is a concise, player-readable account of the actual shot outcome. It does not include a retreat destination coordinate.
- The existing movement response may continue to provide its separate `defensiveFireEvents` data for immediate sound and board-update behavior.

## 5. Acceptance Criteria

- **AC-001**: Given an eligible defender fires at a moving target and has no effect, when movement resolves, then one `noEffect` event with both units, final probability, and random roll is retained under the moving player's turn/player log record.
- **AC-002**: Given a defensive-fire shot forces a target to retreat successfully, when movement resolves, then its event has outcome `retreated`, identifies both units, and its summary does not state a destination coordinate.
- **AC-003**: Given a target cannot complete the forced retreat and is removed, when movement resolves, then its event has outcome `eliminated`, not `retreated`.
- **AC-004**: Given multiple eligible defenders fire at a mover before it leaves the triggering hex, when their events are returned and rendered, then every actual shot appears in resolver order, including no-effect shots.
- **AC-005**: Given a mover retreats before another eligible defender can fire, when movement resolves, then no event is recorded for that defender.
- **AC-006**: Given raw probability `0.2841` and raw roll `0.2317`, when rendered, then the entry displays `28.41%` and `0.23` without changing the raw API values.
- **AC-007**: Given defensive-fire events occurred before a game reload, when the game loads after a browser refresh, then the complete history is returned and rendered under the original moving player's turn/player record.
- **AC-008**: Given a defensive-fire shot resolves, when the movement response is applied, then its sound still plays and affected board-unit availability indicators update.
- **AC-009**: Given the menu is rendered, then neither the Game Stages nor Selected Hex area contains transient defensive-fire message text or the removed reaction-message elements.

## 6. Test Automation Strategy

- **Core unit tests**: Cover durable event creation for no effect, successful retreat, elimination after failed retreat, deterministic multi-shot ordering, skipped later defenders, and retained history.
- **API unit tests**: Verify camelCase serialization, IDs and names, raw probability and roll values, normalized outcomes, summaries, complete full-game history, and continued transient movement-response compatibility.
- **Frontend unit tests**: Verify Game Log block organization, percentage and two-decimal roll formatting, each result text and summary, moving-player grouping, initial-load and state-refresh rendering, removal of reaction-message/status behavior, continued sound handling, and indicator updates.
- **Regression tests**: Run `./server-side-checks.sh` and `npm run test-and-build` from `battle-hexes-web`.

## 7. Rationale & Context

Defensive fire currently appears only as transient messages during movement, which disappear after later actions or page refresh. Persisting each actual shot makes movement consequences explainable to players and agents. The Game Log is the appropriate durable home, while the existing movement-response events remain useful for immediate sound and board synchronization.

## 8. Dependencies & External Integrations

### Data Dependencies

- **DAT-001**: Core defensive-fire resolution results, including firing and target identities, final probability, random roll, actual retreat/elimination effect, and shot order.
- **DAT-002**: The persisted game-log model and full-game-state API contract defined by [Reinforcement Game Event Log](design-game-event-log.md).
- **DAT-003**: Existing movement-response defensive-fire events used for immediate sound and board-update behavior.

No external systems or third-party services are required.

## 9. Examples & Edge Cases

```text
Defensive Fire
Firing unit: Feldwache A
Target unit: Rifle Platoon B
Success probability: 28.41%
Random roll: 0.23
Result: Target retreated
Feldwache A forced Rifle Platoon B to retreat.
```

A no-effect shot remains visible in history. A shot whose target is eliminated after a failed retreat is reported as Target eliminated, even though its immediate game-rule result began as a forced retreat.

## 10. Validation Criteria

The feature is complete when every actual defensive-fire shot is retained and available on game load, the API exposes the specified structured history, the Game Log renders it clearly, transient defensive-fire text areas are removed without regressing sounds or indicators, defensive-fire rules remain unchanged, and the tests in Section 6 pass.

## 11. Related Specifications / Further Reading

- [Reinforcement Game Event Log](design-game-event-log.md)
- [Combat Game Log Events](design-game-log-combat.md)
- [Defensive Fire API Specification](defensive-fire/defensive-fire-3-api.md)

## Open Questions

No questions.
