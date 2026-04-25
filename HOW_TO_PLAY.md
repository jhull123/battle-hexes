# How to Play Battle Hexes

Battle Hexes is a turn-based strategy game played on a hexagonal grid.
Players take turns moving their units across the board and engaging in combat.

## Movement and Combat

Units have a limited number of movement points each turn. They may move to any
adjacent hex, spending one movement point per hex. Movement stops immediately
when a unit enters a hex that is adjacent to an enemy unit. A unit may not move
again until combat around that hex is resolved.

This rule means that movement plans cannot pass through hexes that border enemy
units. If a path would cause a unit to become adjacent to an opponent, the unit
must end its movement on that hex.

### Stacking Limit

Each scenario defines a stacking limit: the maximum number of friendly units
that may occupy the same hex at one time.

A unit may not move into a hex if doing so would exceed that hex's stacking
limit. Enemy units may not occupy the same hex.

## Combat

Combat occurs between adjacent enemy units. Total the attack strength of the attacking units and the defense strength of the defending units, then convert that ratio to the closest supported column on the Combat Results Table (CRT).

After determining the base odds, apply any terrain combat odds shift for the hex occupied by the defender. Terrain shifts modify the odds column, not the unit strengths. A negative shift moves the odds left on the CRT and favors the defender. For example, an attack at 2:1 against a defender in terrain with a -1 shift is resolved on the 1:1 column. If defenders are spread across multiple hexes with different terrain shifts, use the most defensive shift (the lowest value, such as `-2` over `-1` or `0`). Odds cannot shift beyond the leftmost or rightmost CRT column.

Once the final odds column is determined, roll one die and apply the result shown on the CRT.

### Combat Results
Defender Eliminated: the defending unit is removed.
Defender Retreat 2: the defending unit retreats 2 hexes.
Attacker Retreat 2: the attacking unit retreats 2 hexes.
Attacker Eliminated: the attacking unit is removed.
Exchange: both sides take the exchange result defined by the game system.

**Note** Units with zero movement (fixed units such as garrisons) cannot retreat. These units are eliminated when forced to retreat. 

## Defensive Fire

An off-turn unit may fire when an enemy moves into combat position (becomes
adjacent). Each unit can use defensive fire at most once per off turn. A unit
that has defensive fire available has an indicator icon in the upper right
hand corner of its unit counter.

The results of defensive fire are:
- the offensive unit is forced to retreat one hex
- nothing (no effect)

### Eligibility
A unit is eligible only if, on its previous turn, the unit ended the turn with more than one movement point remaining and it was not forced to retreat.

Units with zero movement points as part of their stats (like a 1-1-0 unit) may engage in defensive fire despite never having more than one movement point after each turn.

A unit that conducts defensive fire loses its defensive fire ability for the remainder of that off-turn, regardless of whether the result is retreat or no effect.

Defensive fire eligibility is determined at the end of a unit’s friendly turn and is lost immediately if the unit is forced to retreat before it fires.

Defensive fire status is reset at the start of a player's turn.

### Firing
Defensive fire is resolved immediately during the movement phase when an enemy unit moves adjacent. A defending unit fires automatically when it has defensive fire available and an enemy unit becomes adjacent. If multiple eligible units are in the same hex, each unit resolves defensive fire separately. If any result forces a retreat, the moving unit retreats one hex and its movement ends immediately.

### Effectiveness
Defensive fire is resolved using a probability defined by the scenario.

Final defensive fire chance is calculated as:

    chance = base_probability × unit_modifier × terrain_modifier

- base_probability is defined in the scenario
- unit_modifier is defined on the firing unit (default 1.0)
- terrain_modifier is based on the terrain of the target unit (default 1.0)
- The final chance is clamped between the scenario minimum and maximum

If the defensive fire roll succeeds, the moving unit retreats one hex. Otherwise, there is no effect.

## Ending the Game

Play continues until only one player still has units on the board. When all of
your opponents' forces have been eliminated, the game ends immediately. The
game also ends immediately when the scenario turn limit is reached.
