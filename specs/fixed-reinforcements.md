# Fixed Reinforcements (Implementable Spec)

## Overview

Add scenario-defined reinforcements that enter play on or after a specified
turn at one exact hex. This feature implements only fixed entry locations;
player choice, random entry, zones, and other modes are out of scope.

## Scenario Contract

Add support for an optional top-level `reinforcements` array to scenario JSON. 
Each entry defines one atomic group:

```json
{
  "id": "wehrmacht_stug_column",
  "units": ["StuG. III Zug A", "MG Trupp A"],
  "arrival_turn": 3,
  "entry_location": {
    "mode": "fixed",
    "coords": [0, 16]
  }
}
```

- `id` is a non-empty, scenario-unique identifier.
- `units` is a non-empty list of scenario unit IDs.
- `arrival_turn` is a positive integer.
- `entry_location.mode` must be `fixed`.
- `entry_location.coords` is a board coordinate.
- Omitted `reinforcements` means no reinforcements. Existing scenarios remain
  valid without changes.

## Validation

Scenario loading must reject a reinforcement definition when:

- its ID is duplicate or invalid (empty);
- it has no units, references an unknown unit, or repeats a unit ID;
- `arrival_turn` is not a positive integer less than or equal to the turn limit (if defined);
- its fixed coordinates are out of bounds; or
- a referenced unit is also listed in `hex_data.units` or another reinforcement group.
- units beling to more that one player

A scenario may define units that are never deployed. A defined unit may be
assigned to at most one deployment source.

An arrival turn after the scenario turn limit is valid. That group does not
enter before the game ends and does not keep a player in the game.

## Arrival Rules

- At the start of each new numbered turn, before Player 1 acts, process every
  reinforcement group whose `arrival_turn` is at or before the current turn
  and which has not entered.
- A group enters only if every member can occupy its configured hex at that
  time: the hex contains no enemy units and has capacity for the entire group
  under the normal stacking rule.
- Entry is atomic. If the entire group cannot enter, place none of its units.
- A blocked group remains pending and is retried at the start of each later
  turn. Do not search adjacent hexes or use an alternative location.
- Entered units receive their normal full movement allowance and may act in
  their owner's turn during that turn.
- Entered units are not eligible for defensive fire until they complete a
  friendly turn under the existing eligibility rules.
- Use deterministic processing when multiple due groups contend for the same
  entry hex; scenario declaration order is sufficient.

## Game Status

A player with no on-board units remains active while it has at least one
pending reinforcement that could still arrive before the game ends. Pending
reinforcements must therefore be considered by game-over/elimination checks.

The existing turn-limit and victory/scoring behavior remains authoritative.
A blocked group that has not entered by game end is not placed.

## Required Changes

### `battle_hexes_core`

- Add reinforcement data models to scenario parsing and core scenario domain
  types.
- Preserve reinforcement definitions when loading a scenario.
- Carry pending reinforcement state on the runtime game and deploy groups at
  the turn boundary described above.
- Construct reinforcement units using the same faction, owner, combat stats,
  movement, and defensive-fire configuration as initially placed units.
- Reuse existing occupancy and stacking rules for entry legality.
- Update game-status evaluation so eligible pending reinforcements prevent
  premature player elimination.
- create a new reinforncements validator that is invoked by the current
  scenario validator class.

### API and Web

- No new API or frontend contract is required for this phase.
- Existing board/game responses must show reinforcement units once core
  placement has occurred.
- No arrival notification or reinforcement-selection UI is included.

## Test Plan

- Scenario loader accepts and maps a valid fixed reinforcement group.
- Omitted reinforcements retain current scenario behavior.
- Validation rejects each invalid condition listed above.
- A group is absent before its arrival turn and enters at the start of its
  arrival turn.
- A multi-unit group enters together when capacity permits.
- A group blocked by enemy occupancy or stacking remains entirely off-board
  and enters on a later turn once the hex is legal.
- Multiple due groups contending for an entry hex resolve deterministically.
- Reinforcement units can move on their owner's arrival-turn activation and
  have no premature defensive-fire eligibility.
- A player with only pending, still-possible reinforcements is not eliminated.
- A group scheduled after the turn limit never enters and does not prevent
  normal game completion.

## Game Instructions

Update the `HOW_TO_PLAY.md` file to describe how reinforcements work. Keep the 
updates concise and readable. 

## Non-goals

- Player-selected entry locations or delayed selections.
- Randomized entry, radius/zone entry, alternative hexes, or fallback rules.
- Partial group entry.
- Arrival messages, animations, or dedicated UI.

## Open Questions

No questions.
