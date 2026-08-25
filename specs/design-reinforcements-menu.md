---
title: Reinforcements Game Menu
version: 1.0
date_created: 2026-08-23
tags: [design, api, web, reinforcements]
---

# Introduction

Add a read-only **Reinforcements** area to the existing game-information menu. It gives every player a shared view of scenario reinforcements that have not entered the board.

## 1. Purpose & Scope

This specification covers the core-to-API data required to describe pending reinforcements and their presentation in `battle-hexes-web`.

It applies to scenario-defined fixed reinforcements, including groups delayed because their fixed entry hex could not accept the entire group. It does not change reinforcement deployment rules.

## 2. Definitions

- **Reinforcement group**: The atomic scenario-defined set of units that enter together at one fixed coordinate.
- **Pending**: A reinforcement group that has not entered the board.
- **Scheduled group**: A pending group whose `arrival_turn` is the current turn or a future turn.
- **Delayed group**: A pending group whose `arrival_turn` is before the current turn because a prior deployment attempt could not enter it.
- **Entered**: A group successfully placed on the board by the authoritative core game state.

## 3. Requirements, Constraints & Guidelines

### Visibility and placement

- **REQ-001**: Add a permanent `Reinforcements` section directly after the existing `Game Stages` section in the game-information menu.
- **REQ-002**: Do not add a collapse/expand interaction. The section and its entries are informational only.
- **REQ-003**: If a scenario omits `reinforcements` or defines `reinforcements` as an empty list, do not render the section or its heading.
- **REQ-004**: If the scenario defines one or more reinforcement groups and every group has entered, render the section with `None` directly below its heading and no turn or player grouping headings.
- **REQ-005**: Every player sees the same pending reinforcement information, including opponents' groups.

### Pending-state rules

- **REQ-006**: The server is authoritative for whether a group is pending, scheduled, delayed, or entered. The frontend must not infer this state from board units or scenario definitions.
- **REQ-007**: Render scheduled pending groups under `Turn <arrival turn>`, including groups due on the current turn that have not yet entered.
- **REQ-008**: Do not render entered groups.
- **REQ-009**: Render a pending group whose scheduled arrival turn has passed as delayed, rather than hiding it.
- **REQ-010**: Render each delayed group under `Turn <current turn> (Delayed)`. Do not display the original arrival turn or a blocking reason.
- **REQ-011**: Within the current turn, render on-schedule groups before delayed groups. Render future scheduled turn groups after the current-turn groups in ascending arrival-turn order.
- **REQ-012**: Within each turn/status grouping, render player headings in game player-list order. Within each player heading, preserve scenario declaration order for groups and preserve each group's scenario unit order.

### Entry presentation

- **REQ-013**: Group entries by the owning player name supplied by the game API, for example `Player 2`.
- **REQ-014**: For each unit, render a faction color swatch followed by the unit name and its fixed entry coordinate in the form `(<q>, <r>)`; for example, `StuG. III Zug A (0, 16)`.
- **REQ-015**: Render the coordinate in a smaller font using the visual treatment used for the selected-hex unit movement text (`.selected-unit-moves`).
- **REQ-016**: Resolve each unit's faction color and accessible faction name from its `factionId` and the existing faction metadata in the game payload. Visible information must not rely on color alone.
- **REQ-017**: Match the existing game-menu heading, spacing, typography, and unit-swatch visual language. Do not introduce a new panel design.
- **REQ-018**: Increase the `#menu` CSS width from `280px` to `320px`. With its existing `10px` horizontal padding on each side, the rendered menu width is approximately `340px`.

### Synchronization

- **REQ-019**: Populate the section from the authoritative game payload when loading or resuming a game.
- **REQ-020**: Refresh the rendered reinforcement section after a server-authoritative turn change. It need not independently refresh after non-turn game actions.
- **CON-001**: Core continues to own deployment legality, deployment timing, and the entered state. API schemas serialize already-computed state; schema modules must not execute game-rule evaluation.
- **CON-002**: API JSON names are camelCase. Python internals remain snake_case.

## 4. Interfaces & Data Contracts

Extend the full game response (`GameModel` and all game-state responses that create or replace the client game state) with an optional reinforcement-menu payload. Its presence distinguishes a scenario that defines reinforcement groups from one that does not.

```json
{
  "reinforcements": {
    "pending": [
      {
        "arrivalTurn": 3,
        "status": "scheduled",
        "playerName": "Player 2",
        "units": [
          {
            "unitId": "StuG. III Zug A",
            "name": "StuG. III Zug A",
            "factionId": "Wehrmacht",
            "entryCoordinate": [0, 16]
          },
          {
            "unitId": "MG Trupp A",
            "name": "MG Trupp A",
            "factionId": "Wehrmacht",
            "entryCoordinate": [0, 16]
          }
        ]
      }
    ]
  }
}
```

- `reinforcements` is absent when the scenario has no reinforcement definitions, including an explicit empty list.
- `pending` contains only unentered groups. It is an empty array when every configured group has entered.
- `arrivalTurn` is the immutable scenario arrival turn.
- `status` is `scheduled` when `arrivalTurn >= turnNumber`; it is `delayed` when `arrivalTurn < turnNumber` and the group is still unentered.
- `playerName` and each unit's `unitId`, `name`, `factionId`, and `entryCoordinate` are menu-ready server values. The API resolves player and faction ownership from the scenario/core objects.
- `unitId` is the stable scenario unit identifier. It is included for identity and future linking, but `name` remains required because pending units are not present in the frontend board model or another complete unit catalog.
- `entryCoordinate` is `[q, r]` and corresponds to the group's fixed scenario entry coordinate.
- The frontend resolves faction color and faction name from `factionId` using the existing faction metadata in `players`; do not duplicate `factionName` or `factionColor` in each reinforcement unit entry.
- The API preserves scenario declaration order in `pending`; the frontend uses the existing game player-list order when grouping entries by `playerName`.
- Preserve the existing `GameModel` fields and board-unit contract. This payload neither replaces board units nor reports entered-group history.

The API serialization layer obtains runtime pending/entered state from an explicit core query or read-only core representation. It must not duplicate the core deployment evaluator. The frontend consumes the payload as display data and does not determine statuses locally.

## 5. Acceptance Criteria

- **AC-001**: Given a scenario without `reinforcements` or with an empty array, when its game loads, then no Reinforcements section is rendered.
- **AC-002**: Given Crossroads on D-Day before its turn-3 group enters, when the game payload is rendered, then the section follows Game Stages and shows `Turn 3`, `Player 2`, and the two units in scenario order with Wehrmacht swatches and `(0, 16)` in smaller text.
- **AC-003**: Given an unentered group scheduled for the current turn, when the game state is rendered, then it appears under `Turn <current turn>`.
- **AC-004**: Given an unentered group with an arrival turn earlier than the current turn, when the game state is rendered, then it appears under `Turn <current turn> (Delayed)` and no blocking reason or original arrival turn is shown.
- **AC-005**: Given both scheduled and delayed groups at the current turn, when rendered, then scheduled groups appear before delayed groups and each category retains scenario declaration order.
- **AC-006**: Given a group has entered, when the game payload is rendered, then it does not appear in `pending` or the menu.
- **AC-007**: Given every configured group has entered, when the game loads or advances a turn, then the section shows `None` directly below `Reinforcements` and no turn/player headings.
- **AC-008**: Given a turn-changing response changes pending reinforcement state, when the frontend applies that response, then the menu reflects the returned payload without client-side status calculation.
- **AC-009**: Given a color swatch is rendered, when inspected with assistive technology, then it has an accessible faction-identifying name.
- **AC-010**: Given the game menu is rendered, when its layout is measured, then its CSS content width is `320px` and its existing padding remains intact.

## 6. Test Automation Strategy

- **Core unit tests**: Cover a read-only pending-reinforcement representation for scheduled, delayed, and entered groups without changing existing deployment-rule coverage.
- **API unit tests**: Verify camelCase serialization, absent payload for omitted/empty definitions, pending scheduled entries, delayed entries, and an empty `pending` array after all entries arrive.
- **Frontend unit tests**: Extend the menu DOM fixture and test section placement, hidden state, `None`, turn/player grouping, scenario order, delayed labels, coordinate styling, faction swatches/accessibility, initial load, turn-response refresh, and the widened menu CSS rule.
- **Regression tests**: Run `./server-side-checks.sh` and `npm test` from `battle-hexes-web`.

## 7. Rationale & Context

Reinforcements are currently visible only after deployment as ordinary board units. Showing the authoritative pending schedule gives players useful shared planning information without exposing deployment controls or duplicating game rules in the browser. A delayed status prevents a blocked group from disappearing simply because its original scheduled turn passed.

## 8. Dependencies & External Integrations

### Data Dependencies

- **DAT-001**: Scenario reinforcement definitions, faction metadata, unit definitions, and faction-to-player assignments.
- **DAT-002**: Core runtime reinforcement group state, specifically whether each group has entered.

### Technology Platform Dependencies

- **PLT-001**: The FastAPI game-response schema and the existing p5.js web menu/model synchronization path.

No external systems or third-party services are required.

## 9. Examples & Edge Cases

```text
Reinforcements

Turn 3
Player 2
[Wehrmacht swatch] StuG. III Zug A (0, 16)
[Wehrmacht swatch] MG Trupp A (0, 16)

Turn 5 (Delayed)
Player 2
[Wehrmacht swatch] StuG. III Zug A (0, 16)
```

The coordinate uses reduced text size; the text representation above does not convey that styling.

When all configured groups have entered:

```text
Reinforcements
None
```

## 10. Validation Criteria

The feature is complete when the API contract is populated from authoritative runtime state, the web menu meets every acceptance criterion, existing game behavior remains unchanged, and the test commands in Section 6 pass.

## 11. Related Specifications / Further Reading

- [Fixed Reinforcements](fixed-reinforcements.md)
- [HOW_TO_PLAY](../HOW_TO_PLAY.md)

## Open Questions

No questions.
