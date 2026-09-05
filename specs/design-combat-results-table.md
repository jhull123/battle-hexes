---
title: Combat Results Table Reference
version: 1.0
date_created: 2026-09-05
tags: [design, core, api, web, combat, crt]
---

# Introduction

Expose the authoritative Combat Results Table (CRT) in the full game-state API and render it as the final section of the game menu. Players receive an in-game rules reference, and agents receive the same structured combat-resolution reference without inferring it from combat outcomes.

## 1. Purpose & Scope

This specification covers the CRT reference data from its authoritative core definition through full-game API serialization and web-menu presentation.

It does not change CRT columns, result mappings, die rolling, combat resolution, scenario configuration, or add a dedicated rules endpoint.

## 2. Definitions

- **CRT**: Combat Results Table. The ordered mapping from an odds column and die roll to a combat result.
- **Odds column**: The attacker-to-defender ratio used to select a CRT row, represented as `[attacker, defender]` in the API and `<attacker>:<defender>` in the UI.
- **Automatic odds column**: The extreme `1:7` or `7:1` column whose outcome is automatic and does not use a die roll.
- **Result code**: The stable programmatic name of a combat result, such as `DEFENDER_RETREAT_2`.
- **Result text**: The player-readable name of a combat result, such as `Defender Retreat 2 Hexes`.

## 3. Requirements, Constraints & Guidelines

### Authoritative rules data

- **REQ-001**: Core remains the single authoritative source of CRT odds columns and outcomes.
- **REQ-002**: Expose every current CRT odds column in ascending attacker advantage order, including automatic `1:7` and `7:1` columns.
- **REQ-003**: Expose the six die-roll columns `1` through `6` for normal CRT rows, using stable result codes and player-readable result text.
- **REQ-004**: Expose each automatic odds column as one automatic result, rather than fabricating six die-roll results.
- **CON-001**: This feature must not duplicate or alter the core combat solver's rules. The API reference is a read-only projection of those rules.

### API contract

- **REQ-005**: Add an always-present `combatResultsTable` property to `GameModel` and all existing full-game-state responses that create or replace client game state.
- **REQ-006**: The API returns the same CRT to every player and agent. It is not filtered by player, scenario, game state, or combat phase.
- **REQ-007**: Serialize CRT reference data on full-game-state responses only. Do not add a dedicated CRT or rules endpoint in this phase.
- **REQ-008**: Keep the contract structured. Clients and agents must use result codes for programmatic interpretation and result text for display; neither should parse a rendered table or display string.
- **CON-002**: HTTP JSON uses camelCase. Python internals use snake_case.

### Web menu

- **REQ-009**: Add a permanent `Combat Results Table` section as the final section in the scrollable game-information menu, after Navigation.
- **REQ-010**: Render a semantic HTML table with an `Odds` column and die-roll columns `1` through `6`.
- **REQ-011**: Render normal rows with the odds label and the result text for each die-roll column.
- **REQ-012**: Render automatic `1:7` and `7:1` rows with their odds label and one clearly labeled automatic-result cell spanning the six die-roll columns.
- **REQ-013**: Render the table exclusively from `combatResultsTable` received in game state. Do not duplicate CRT mappings in frontend code.
- **REQ-014**: Fit the table within the existing menu width without horizontal overflow. Compact typography and normal wrapping are acceptable; do not change the menu width for this feature.
- **REQ-015**: Provide a table caption or equivalent accessible name, and use column headers that identify odds and each die-roll value.

## 4. Interfaces & Data Contracts

Add the following property to the full game response:

```json
{
  "combatResultsTable": {
    "dieRolls": [1, 2, 3, 4, 5, 6],
    "rows": [
      {
        "odds": [1, 7],
        "automaticResult": {
          "code": "ATTACKER_ELIMINATED",
          "text": "Attacker Eliminated"
        }
      },
      {
        "odds": [1, 6],
        "results": [
          {
            "code": "ATTACKER_ELIMINATED",
            "text": "Attacker Eliminated"
          },
          {
            "code": "ATTACKER_ELIMINATED",
            "text": "Attacker Eliminated"
          },
          {
            "code": "ATTACKER_RETREAT_2",
            "text": "Attacker Retreat 2 Hexes"
          },
          {
            "code": "ATTACKER_ELIMINATED",
            "text": "Attacker Eliminated"
          },
          {
            "code": "ATTACKER_ELIMINATED",
            "text": "Attacker Eliminated"
          },
          {
            "code": "ATTACKER_ELIMINATED",
            "text": "Attacker Eliminated"
          }
        ]
      },
      {
        "odds": [7, 1],
        "automaticResult": {
          "code": "DEFENDER_ELIMINATED",
          "text": "Defender Eliminated"
        }
      }
    ]
  }
}
```

- `dieRolls` is always `[1, 2, 3, 4, 5, 6]` and defines normal-row result order.
- `rows` contains every supported odds column in the same ascending order used by core combat resolution: `1:7` through `7:1`.
- A normal row has `results`, exactly one result object per value in `dieRolls`, and omits `automaticResult`.
- An automatic row has `automaticResult` and omits `results`.
- A result object's `code` is the stable core result enum name; `text` is its player-readable enum value.
- The client displays the automatic result as `Automatic: <text>`.

## 5. Acceptance Criteria

- **AC-001**: Given any game loads, when its full game state is returned, then it includes `combatResultsTable` with die rolls, every CRT row, result codes, and result text.
- **AC-002**: Given normal row `1:6`, when serialized, then it has six results in die-roll order and each matches the authoritative core CRT mapping.
- **AC-003**: Given automatic row `1:7` or `7:1`, when serialized, then it has one automatic result and no fabricated six-entry `results` array.
- **AC-004**: Given the Game Model replaces client state on initial load or refresh, when the menu renders, then the CRT is rendered from the returned API payload.
- **AC-005**: Given the menu is inspected, then Combat Results Table is the last menu section and its normal rows have Odds and die-roll headers `1` through `6`.
- **AC-006**: Given an automatic row is rendered, then its result is visibly labeled as automatic and spans the six die-roll columns.
- **AC-007**: Given the table is rendered at the existing menu width, then it has no horizontal overflow and remains legible.
- **AC-008**: Given an agent receives full game state, then it can determine the result code for a supplied normal odds column and die-roll value without parsing player-readable text.

## 6. Test Automation Strategy

- **Core unit tests**: Verify the CRT projection includes all odds columns, normal-row mappings, automatic outcomes, ordering, codes, and text from the authoritative solver definitions.
- **API unit tests**: Verify camelCase serialization, complete table presence on `GameModel`, result-array length, automatic-row shape, and no change to existing combat resolution payloads.
- **Frontend unit tests**: Verify final-section placement, API-driven rendering, normal and automatic rows, headers, accessible caption/name, and no horizontal overflow styling.
- **Regression tests**: Run `./server-side-checks.sh` and `npm run test-and-build` from `battle-hexes-web`.

## 7. Rationale & Context

The CRT is static, compact reference data. Including it in the existing full game-state payload keeps a loaded game self-contained for the UI and agents and follows the established pattern for static scenario metadata. The payload is small enough that a dedicated endpoint and client cache are unnecessary now. If future rules reference data becomes materially larger, it can be moved to a cacheable versioned rules endpoint without changing the CRT's structured representation.

## 8. Dependencies & External Integrations

### Data Dependencies

- **DAT-001**: The core `CombatSolver` CRT odds columns, normal result mappings, and automatic extreme-odds outcomes.
- **DAT-002**: Existing `GameModel` full-state serialization and frontend game-state replacement path.

No external systems or third-party services are required.

## 9. Examples & Edge Cases

```text
Combat Results Table

Odds   1                    2                    3                    4                    5                    6
1:7    Automatic: Attacker Eliminated
1:6    Attacker Eliminated  Attacker Eliminated  Attacker Retreat 2…  Attacker Eliminated  Attacker Eliminated  Attacker Eliminated
7:1    Automatic: Defender Eliminated
```

The UI may wrap long result text within cells. Automatic odds columns never display or require a die roll.

## 10. Validation Criteria

The feature is complete when the API and UI expose the exact authoritative CRT, agents can consume its structured result codes, the table remains accessible and readable at existing menu dimensions, combat behavior is unchanged, and the tests in Section 6 pass.

## 11. Related Specifications / Further Reading

- [Combat Game Log Events](design-game-log-combat.md)
- [Terrain Modifies Combat Odds](terrain-combat-odds-shift.md)
- [Reinforcement Game Event Log](design-game-event-log.md)

## Open Questions

No questions.
