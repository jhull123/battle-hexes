---
title: Reinforcement Game Event Log
version: 1.0
date_created: 2026-08-29
tags: [design, core, api, web, game-log, reinforcements]
---

# Introduction

Add a shared, read-only Game Log section to the game-information menu. The first supported records describe each reinforcement arrival attempt. The log must preserve its complete history in game state so it is available through the existing game API after loading or refreshing a game.

## 1. Purpose & Scope

This specification covers persisted reinforcement arrival events from core game resolution through API serialization and the web menu.

It does not add other event categories, interactive log controls, scrolling behavior, dice or odds records, or changes to reinforcement deployment rules.

## 2. Definitions

- **Game event**: An immutable historical record of a completed game-state decision.
- **Reinforcement arrival attempt**: One authoritative evaluation of one due, unentered reinforcement group at a turn boundary.
- **Arrived event**: An arrival attempt that placed the entire reinforcement group on its configured entry hex.
- **Blocked event**: An arrival attempt that placed none of the group because the configured entry hex could not accept the entire group.
- **Complete game log**: Every event created since the game was initialized, including events that occurred before a game is loaded or the browser page is refreshed.

## 3. Requirements, Constraints & Guidelines

### Core event history

- **REQ-001**: Core owns recording reinforcement arrival events when it resolves reinforcement deployment.
- **REQ-002**: Record exactly one event for every due, unentered reinforcement group evaluated during a turn-boundary deployment pass.
- **REQ-003**: An event records the current turn number, owning player, total number of units in the group, configured entry coordinate, and outcome (`arrived` or `blocked`).
- **REQ-004**: Record an `arrived` event only after the complete group is placed. Record a `blocked` event when the group is not placed. Do not infer events later from pending or board state.
- **REQ-005**: A blocked group produces another blocked or arrived event for each later turn in which it is retried.
- **REQ-006**: Preserve event creation order and retain the complete log as part of the authoritative runtime game state. Events must not be discarded when groups enter, turns advance, or a player is eliminated.
- **CON-001**: This feature must not change reinforcement timing, entry legality, atomic deployment, retry behavior, game-status evaluation, or board state.

### API contract

- **REQ-007**: Add the complete log to `GameModel` and therefore every existing response that supplies full game state to the client. Do not add a dedicated log endpoint in this phase.
- **REQ-008**: The API exposes the initial log as reinforcement-specific data. Do not introduce a generic event type, event discriminator, dice-roll fields, odds fields, or placeholders for future event categories.
- **REQ-009**: Return turn-and-player game-log records newest first. Within each record, return its reinforcement events newest first.
- **REQ-010**: All players receive the same complete log without player-specific filtering.
- **CON-002**: API schemas serialize already-recorded core events and must not execute deployment legality or reconstruct history.
- **CON-003**: HTTP JSON uses camelCase. Python internals use snake_case.

### Web menu

- **REQ-011**: Add a permanent `Game Log` section directly after `Game Stages` and before `Reinforcements` in the existing game-information menu.
- **REQ-012**: Render entries in newest-first order. Do not render a heading or placeholder for turns with no events.
- **REQ-013**: Group consecutive entries with the same turn number and player under one bold heading in the form `Turn <turn> - <player name>`.
- **REQ-014**: Render arrived entries as `Reinforcements arrived - <unit count> units at (<q>, <r>)` and blocked entries as `Reinforcements blocked - <unit count> units at (<q>, <r>)`.
- **REQ-015**: Use singular `unit` when the count is one.
- **REQ-016**: The section is informational only. Do not add scrolling, filtering, expansion, unread state, controls, or client-side event generation.
- **REQ-017**: Render the complete returned log both on initial game load and whenever an existing full-game-state response replaces or updates client state.
- **REQ-018**: Increase the existing `#menu` CSS content width by exactly `40px`, from `320px` to `360px`. Apply the existing responsive behavior unchanged; no separate desktop/mobile width is required.

## 4. Interfaces & Data Contracts

Add an always-present `gameLog` array to the full game response. Each item is a turn-and-player record. The array is empty when no reinforcement arrival attempts have occurred. This shape directly answers which reinforcement events occurred for a player during a turn.

```json
{
  "gameLog": [
    {
      "turnNumber": 3,
      "playerName": "Player 2",
      "events": {
        "reinforcements": [
          {
            "outcome": "arrived",
            "unitCount": 2,
            "entryCoordinate": [0, 16]
          },
          {
            "outcome": "arrived",
            "unitCount": 1,
            "entryCoordinate": [0, 0]
          }
        ]
      }
    },
    {
      "turnNumber": 3,
      "playerName": "Player 1",
      "events": {
        "reinforcements": [
          {
            "outcome": "blocked",
            "unitCount": 2,
            "entryCoordinate": [0, 0]
          }
        ]
      }
    }
  ]
}
```

- `gameLog` contains one record for each turn/player combination that has one or more loggable events. It is newest-first as defined in REQ-009.
- A record's `turnNumber` is the turn in which its events were evaluated.
- A record's `playerName` is the game player name that owns the recorded reinforcement groups.
- `events.reinforcements` contains one entry per reinforcement arrival attempt for that player in that turn.
- A reinforcement event's `outcome` is exactly `arrived` or `blocked`.
- A reinforcement event's `unitCount` is the number of units in the evaluated group, not the number of units presently at the hex.
- A reinforcement event's `entryCoordinate` is the fixed entry coordinate as `[q, r]`.
- The API supplies structured values; the frontend creates the user-facing sentence and singular/plural label.

## 5. Acceptance Criteria

- **AC-001**: Given a new game with no evaluated reinforcement groups, when its full game state loads, then `gameLog` is an empty array and the Game Log section is empty.
- **AC-002**: Given a due two-unit group enters at `[0, 16]` for Player 2 on turn 3, when deployment resolves, then one arrived event is retained and the API exposes its turn, player, count, coordinate, and outcome.
- **AC-003**: Given a due two-unit group cannot enter at `[0, 0]` for Player 3 on turn 3, when deployment resolves, then one blocked event is retained and the API exposes its turn, player, count, coordinate, and outcome.
- **AC-004**: Given a previously blocked group is retried on turn 4, when it remains blocked or arrives, then the new event is retained in addition to the turn-3 blocked event.
- **AC-005**: Given events for Player 2 and Player 3 on turn 3, when rendered, then each player has a distinct `Turn 3 - Player <n>` heading and their event lines follow the required text format.
- **AC-006**: Given a later event exists, when the log is returned and rendered, then it appears before older events and no empty-turn placeholder is shown.
- **AC-007**: Given events already occurred, when the game is loaded again after a browser refresh, then the API response and Game Log show the complete prior history.
- **AC-008**: Given the menu is rendered, when its content width is measured, then `#menu` is `360px` wide while existing padding and responsive rules remain in effect.

## 6. Test Automation Strategy

- **Core unit tests**: Verify event creation for successful and blocked attempts, repeated blocked retries, successful retry after a block, stable creation ordering, and retained history.
- **API unit tests**: Verify camelCase serialization, empty initial log, full retained history, newest-first ordering, and the exact reinforcement-specific payload fields.
- **Frontend unit tests**: Verify section placement, empty-log rendering, newest-first turn/player grouping, arrived and blocked text including singular/plural units and coordinates, state refresh, and the menu-width CSS rule.
- **Regression tests**: Run `./server-side-checks.sh` and `npm run test-and-build` from `battle-hexes-web`.

## 7. Rationale & Context

Reinforcement attempts are useful shared history for players and for agents that otherwise must infer changes from board snapshots. Persisting the authoritative outcomes avoids that inference and ensures refreshes do not erase historical context. The narrow initial contract supports the immediate use case without prematurely defining a generic event taxonomy for combat odds, dice rolls, or future event types.

## 8. Dependencies & External Integrations

### Data Dependencies

- **DAT-001**: Core reinforcement deployment results, group ownership, unit membership, turn number, and fixed entry coordinate.
- **DAT-002**: Existing full game-state serialization and frontend game-state application path.

No external systems or third-party services are required.

## 9. Examples & Edge Cases

```text
Game Log

Turn 3 - Player 2
Reinforcements arrived - 2 units at (0, 16)
Reinforcements arrived - 1 unit at (0, 0)

Turn 3 - Player 3
Reinforcements blocked - 2 units at (0, 0)
```

A turn with no arrival attempts has no log entry or heading. A group blocked on multiple turns creates one blocked entry per attempt rather than replacing its prior entries.

## 10. Validation Criteria

The feature is complete when core retains authoritative reinforcement-attempt history, the existing full game API returns it after initial load and refresh, the web menu renders the specified history between Game Stages and Reinforcements, deployment behavior is unchanged, and the tests in Section 6 pass.

## 11. Related Specifications / Further Reading

- [Reinforcements Game Menu](design-reinforcements-menu.md)
- [Fixed Reinforcements](fixed-reinforcements.md)
- [HOW_TO_PLAY](../HOW_TO_PLAY.md)

## Open Questions

No questions.
