---
title: Combat Game Log Events
version: 1.0
date_created: 2026-09-04
tags: [design, core, api, web, game-log, combat]
---

# Introduction

Extend the persisted Game Log with a readable, complete record for each normal combat-phase resolution. Combat records make the resolved participants, odds calculation, die roll, CRT result, and resulting losses or retreats available to players and agents after the fact.

## 1. Purpose & Scope

This specification extends the turn/player Game Log contract in [Reinforcement Game Event Log](design-game-event-log.md) with `events.combat`.

It applies only to normal combat-phase resolution. Defensive fire, future modifiers beyond defender terrain, log controls, and changes to combat rules are out of scope.

## 2. Definitions

- **Combat event**: One immutable record of a normal combat resolution between its participating attacker and defender groups.
- **Attacking player**: The current player resolving the combat phase. Combat events belong to this player’s turn/player log record.
- **Base odds**: The combat-results-table (CRT) column selected from the attackers’ total attack factor and defenders’ total defense factor before modifiers.
- **Modified odds**: The final CRT column after applying the defender-terrain odds shift and normal CRT-column clamping.
- **CRT outcome**: The named result selected from the CRT, such as `Defender Retreat 2 Hexes` or `Exchange`.
- **Eliminated unit**: A participant removed from the board by the resolved combat, including a unit eliminated because it could not complete a required retreat.
- **Retreated unit**: A participant that successfully completed the retreat required by the resolved combat.

## 3. Requirements, Constraints & Guidelines

### Core history

- **REQ-001**: Core records one combat event immediately after each normal combat resolution has applied all board effects.
- **REQ-002**: A combat event records the attackers and defenders as they participated before the board is updated; eliminated and retreated lists reflect the actual post-resolution effects.
- **REQ-003**: Record the base odds, modified odds, applied defender-terrain modifier, die roll, CRT outcome code and text, and a player-readable result summary.
- **REQ-004**: A participant record includes its display name and attack, defense, and movement values at combat resolution time.
- **REQ-005**: Record an eliminated unit once, even when it was eliminated after failing a required retreat. Record a successfully retreated unit once. A unit cannot appear in both lists.
- **REQ-006**: Retain combat events in the same complete, authoritative game history used by reinforcement events. They remain available after turn changes, game completion, game load, and browser refresh.
- **REQ-007**: A combat event belongs to the current attacking player’s turn/player record, regardless of the defender’s owner.
- **CON-001**: Do not record defensive-fire events in this phase.
- **CON-002**: Do not alter combat identification, participant selection, odds calculation, terrain selection, die rolling, CRT resolution, retreat behavior, elimination behavior, scoring, or game-status behavior.

### API contract

- **REQ-008**: Extend each existing `gameLog` record’s `events` object with a `combat` array. It is empty when that turn/player record contains no normal combat resolutions.
- **REQ-009**: Return combat events newest first. Preserve that ordering in the Game Log panel.
- **REQ-010**: Return identical complete combat history to every player. Do not filter participants, results, terrain, odds, or die rolls by viewer.
- **CON-003**: API schemas serialize recorded core history. They must not rerun combat logic or infer combat effects from current board state.
- **CON-004**: HTTP JSON uses camelCase. Python internals use snake_case.

### Presentation

- **REQ-011**: Render each combat event as a visually distinct, readable block in the existing Game Log section under its attacking player’s `Turn <turn> - <player name>` heading.
- **REQ-012**: The block shows `Combat` as its title, followed by labeled `Attacking` and `Defending` participant lines.
- **REQ-013**: Render every participant as `<unit name> <attack>-<defense>-<movement>`. The stat triplet uses the existing smaller secondary-text treatment.
- **REQ-014**: Render `Base odds: <attacker>:<defender>`, `Modified odds: <attacker>:<defender>`, and `Die roll: <value>` as separate labeled lines.
- **REQ-015**: Render `Modified by defender terrain: <terrain name> (<signed shift> odds shift)`. A zero modifier uses `(+0 odds shift)`.
- **REQ-016**: Render the CRT outcome as `Result: <CRT outcome text>`, then render the player-readable result summary.
- **REQ-017**: When nonempty, render `Eliminated: <unit names>` and `Retreated: <unit names>` as separate lines. Do not show retreat destination coordinates.
- **REQ-018**: Do not render empty eliminated or retreated labels.

## 4. Interfaces & Data Contracts

The existing `gameLog` turn/player record gains `events.combat`. The following record shows a normal combat resolved by Player 2 in turn 3:

```json
{
  "turnNumber": 3,
  "playerName": "Player 2",
  "events": {
    "reinforcements": [],
    "combat": [
      {
        "attackers": [
          {
            "name": "Unit A",
            "attack": 4,
            "defense": 4,
            "movement": 2
          },
          {
            "name": "Unit B",
            "attack": 2,
            "defense": 2,
            "movement": 4
          }
        ],
        "defenders": [
          {
            "name": "Unit C",
            "attack": 3,
            "defense": 3,
            "movement": 3
          }
        ],
        "baseOdds": [3, 1],
        "modifiedOdds": [2, 1],
        "defenderTerrain": {
          "name": "Woods",
          "oddsShift": -1
        },
        "dieRoll": 4,
        "result": {
          "code": "DEFENDER_RETREAT_2",
          "text": "Defender Retreat 2 Hexes",
          "summary": "Unit C retreated 2 hexes."
        },
        "eliminatedUnits": [],
        "retreatedUnits": ["Unit C"]
      }
    ]
  }
}
```

- `events.combat` contains one entry per normal combat resolution for its record’s player and turn.
- `attackers` and `defenders` preserve the resolved participant order and use pre-resolution unit values.
- `baseOdds` and `modifiedOdds` are `[attacker, defender]` CRT ratios.
- `defenderTerrain.name` identifies the defender terrain that supplied the applied shift. When multiple defender hexes are evaluated, use the terrain whose shift was selected by the existing authoritative combat rule; equal shifts use existing participant evaluation order.
- `defenderTerrain.oddsShift` is the applied shift before CRT-column clamping.
- `dieRoll` is the rolled die value. For automatic extreme-odds outcomes that do not roll, it retains the combat solver’s existing sentinel value.
- `result.code` is the stable CRT result code, `result.text` is the CRT outcome text, and `result.summary` is a concise player-readable account of actual effects.
- `eliminatedUnits` and `retreatedUnits` contain unit display names only, in the order their effects were resolved.

## 5. Acceptance Criteria

- **AC-001**: Given Player 2 resolves a normal combat on turn 3, when its result is applied, then one combat event is retained under Player 2’s turn-3 game-log record.
- **AC-002**: Given a combat with two attackers and one defender, when its event is returned, then it includes each pre-resolution participant’s name and attack, defense, and movement values.
- **AC-003**: Given base odds `3:1` and defender terrain shift `-1`, when combat resolves, then the event returns `baseOdds` `[3, 1]`, `modifiedOdds` `[2, 1]`, and the selected defender terrain with shift `-1`.
- **AC-004**: Given a defender retreat result where the defender successfully retreats, when the event is returned and rendered, then it contains the CRT outcome, a player-readable summary, the defender in `retreatedUnits`, and no retreat destination coordinate.
- **AC-005**: Given a unit is eliminated during combat or after failing a required retreat, when the event is returned, then the unit appears once in `eliminatedUnits` and not in `retreatedUnits`.
- **AC-006**: Given a combat has no eliminations or retreats, when rendered, then neither the Eliminated nor Retreated line is displayed.
- **AC-007**: Given several normal combats resolve for one player in one turn, when the Game Log is returned and rendered, then they appear as separate combat blocks in newest-first order under that player’s one turn heading.
- **AC-008**: Given a combat occurred before a game reload, when the game is loaded after a browser refresh, then the complete combat record is returned and rendered with the existing reinforcement history.
- **AC-009**: Given defensive fire resolves, when the game log is returned, then no defensive-fire event is present in `events.combat`.

## 6. Test Automation Strategy

- **Core unit tests**: Cover event creation with pre-resolution participants, unmodified and terrain-modified odds, rolled and automatic outcomes, elimination, successful retreat, failed retreat elimination, and retained history.
- **API unit tests**: Verify the nested camelCase contract, participant stats, terrain explanation, result fields, effects lists, ordering, and complete game-load history.
- **Frontend unit tests**: Verify combat-block organization, small stat styling, odds and die-roll lines, terrain explanation, result summary, optional effects lines, turn/player grouping, and refresh rendering.
- **Regression tests**: Run `./server-side-checks.sh` and `npm run test-and-build` from `battle-hexes-web`.

## 7. Rationale & Context

Combat is currently difficult to reconstruct from later board state, particularly when units retreat or are eliminated. Capturing both the calculation inputs and actual outcomes makes resolution explainable to players and supplies agents with the information needed to understand state transitions. The presentation separates participants, calculation, and outcome so a detailed entry remains scannable.

## 8. Dependencies & External Integrations

### Data Dependencies

- **DAT-001**: Authoritative core combat resolution results, pre-resolution participants, defender terrain selection, and actual board effects.
- **DAT-002**: The persisted game-log model and full-game-state API contract defined by [Reinforcement Game Event Log](design-game-event-log.md).

No external systems or third-party services are required.

## 9. Examples & Edge Cases

```text
**Combat: Defender Retreat 2 Hexes**

Attacking: Unit A 4-4-2, Unit B 2-2-4
Defending: Unit C 3-3-3
Base odds: 3:1
Modified odds: 2:1
Modified by defender terrain: Woods (-1 odds shift)
Die roll: 4
```

The stat triplets use smaller text in the UI. No result event is recorded for a combat candidate skipped because a participant was already removed before it could resolve.

## 10. Validation Criteria

The feature is complete when each normal combat resolution is retained as an authoritative event, the full game API returns it after reload, the Game Log presents all requested calculation and outcome data clearly, defensive fire is excluded, combat rules remain unchanged, and the tests in Section 6 pass.

## 11. Related Specifications / Further Reading

- [Reinforcement Game Event Log](design-game-event-log.md)
- [Terrain Modifies Combat Odds](terrain-combat-odds-shift.md)
- [Combat Zero Movement Retreat Rule](combat-zero-movement-retreat-rule.md)

## Open Questions

No questions.
