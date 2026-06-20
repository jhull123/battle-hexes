# API Naming/Casing Inventory

This inventory supports phase 1 of `specs/naming-casing-cleanup.md`. It lists
API request and response schema fields and their canonical HTTP JSON keys.
Python model attributes remain `snake_case`; the HTTP boundary is `camelCase`.

## Request Schemas

### `CreateGameRequest`

| Python attribute | HTTP JSON key |
| --- | --- |
| `scenario_id` | `scenarioId` |
| `player_types` | `playerTypes` |

### `SparseBoard`

| Python attribute | HTTP JSON key |
| --- | --- |
| `units` | `units` |
| `last_combat_results` | `lastCombatResults` |
| `scores` | `scores` |

### `SparseUnit`

| Python attribute | HTTP JSON key |
| --- | --- |
| `id` | `id` |
| `row` | `row` |
| `column` | `column` |
| `defensive_fire_available` | `defensiveFireAvailable` |

## Response Schemas

### Game payload

| Python attribute / route metadata | HTTP JSON key |
| --- | --- |
| `id` | `id` |
| `players` | `players` |
| `board` | `board` |
| `objectives` | `objectives` |
| `scores` | `scores` |
| `turn_limit` | `turnLimit` |
| `turn_number` | `turnNumber` |
| `scenario_id` route metadata | `scenarioId` |
| `scenario.name` route metadata | `scenarioName` |
| `scenario.stacking_limit` route metadata | `stackingLimit` |
| `player_type_ids` route metadata | `playerTypeIds` |

### Board payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `rows` | `rows` |
| `columns` | `columns` |
| `units` | `units` |
| `terrain` | `terrain` |
| `road_types` | `roadTypes` |
| `road_paths` | `roadPaths` |

### Road path payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `type` | `type` |
| `path` | `path` |
| `row` | `row` |
| `column` | `column` |

### Unit payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `id` | `id` |
| `name` | `name` |
| `faction_id` | `factionId` |
| `type` | `type` |
| `attack` | `attack` |
| `echelon` | `echelon` |
| `defense` | `defense` |
| `move` | `move` |
| `row` | `row` |
| `column` | `column` |
| `defensive_fire_available` | `defensiveFireAvailable` |

### Terrain payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `default` | `default` |
| `types` | `types` |
| `hexes` | `hexes` |
| `name` | `name` |
| `color` | `color` |
| `move_cost` | `moveCost` |
| `combat_odds_shift` | `combatOddsShift` |
| `row` | `row` |
| `column` | `column` |
| `terrain` | `terrain` |

### Movement response payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `game` | `game` |
| `plans` | `plans` |
| `sparse_board` | `sparseBoard` |
| `defensive_fire_events` | `defensiveFireEvents` |
| `scores` | `scores` |
| `turn_limit` | `turnLimit` |
| `turn_number` | `turnNumber` |

### Defensive fire event payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `firing_unit_id` | `firingUnitId` |
| `target_unit_id` | `targetUnitId` |
| `trigger_hex` | `triggerHex` |
| `target_hex_before` | `targetHexBefore` |
| `outcome` | `outcome` |
| `retreat_destination` | `retreatDestination` |
| `spent_defensive_fire` | `spentDefensiveFire` |
| `probability` | `probability` |
| `roll` | `roll` |
| `message` | `message` |

### Combat result payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `combat_result_code` | `combatResultCode` |
| `combat_result_text` | `combatResultText` |
| `odds` | `odds` |
| `base_odds` | `baseOdds` |
| `final_odds` | `finalOdds` |
| `die_roll` | `dieRoll` |
| `no_retreat_unit_ids` | `noRetreatUnitIds` |

### Scenario list payload

| Python attribute | HTTP JSON key |
| --- | --- |
| `id` | `id` |
| `name` | `name` |
| `description` | `description` |
| `victory` | `victory` |
| `method` | `method` |
| `scoring_side` | `scoringSide` |
| `stacking_limit` | `stackingLimit` |

### Player and player type payloads

| Python attribute | HTTP JSON key |
| --- | --- |
| `name` | `name` |
| `type` | `type` |
| `factions` | `factions` |
| `id` | `id` |
| `color` | `color` |
| `sounds` | `sounds` |

## Scenario JSON Regression Scope

Scenario authoring JSON under `battle_hexes_core/src/battle_hexes_core/scenarios/`
remains `snake_case`. Loader regression coverage should keep exercising keys
such as `move_cost`, `combat_odds_shift`, `road_types`, and `edge_move_cost`.
