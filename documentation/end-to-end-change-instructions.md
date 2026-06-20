# End-to-End Scenario Property Change Instructions

This guide documents the path a new scenario-file property usually takes through Battle Hexes so it can be authored in JSON, loaded by the core package, serialized by the API, and consumed by the frontend.

Use it when adding a property to one of the scenario JSON files under `battle_hexes_core/src/battle_hexes_core/scenarios/`. The exact files depend on where the property belongs (scenario-level metadata, faction, unit, terrain type, road, objective, or hex data), but the same end-to-end pattern applies.

## Data Flow Overview

1. **Scenario JSON** defines the source value in `battle_hexes_core/src/battle_hexes_core/scenarios/*.json`.
2. **Core loader validation models** in `battle_hexes_core/src/battle_hexes_core/scenario/scenario_loader.py` parse and validate the JSON payload.
3. **Core scenario dataclasses** in `battle_hexes_core/src/battle_hexes_core/scenario/scenario.py` hold the validated, domain-facing scenario value.
4. **Game creation / domain application** maps scenario data into runtime game, board, unit, terrain, road, objective, scoring, or rules objects when the property affects gameplay.
5. **API Pydantic schemas** in `battle_hexes_api/src/battle_hexes_api/schemas/` expose the value to clients.
6. **API route serialization** in `battle_hexes_api/src/battle_hexes_api/main.py` may adapt field names or add top-level fields before returning JSON.
7. **Frontend service layer** fetches the API JSON without much transformation.
8. **Frontend model creation** in `battle-hexes-web/src/model/game-creator.js` converts response JSON into JavaScript model objects.
9. **Frontend model classes, renderers, and UI** store, expose, and use the value.
10. **Tests and mock data** must be updated at each boundary so future changes do not silently break serialization.

## Step-by-Step Checklist

### 1. Decide the property's scope and wire format

Before editing code, decide:

- Which scenario JSON block owns the property:
  - Top-level scenario metadata, such as `turn_limit` or `stacking_limit`.
  - `victory` block.
  - `defensive_fire` block.
  - `factions` entries.
  - `units` entries.
  - `terrain_types` entries.
  - `road_types` or `roads` entries.
  - `hex_data` entries.
  - `objectives` entries.
- Whether the JSON/API field should be `snake_case`, `camelCase`, or both.
  - Current scenario JSON and most Python schemas use `snake_case`.
  - The API sometimes converts selected response fields to `camelCase` for frontend use, such as `scenarioId`, `stackingLimit`, `turnLimit`, and `turnNumber`.
- Whether the property is required or optional.
- The default for existing scenario files.
- Validation rules (integer vs float, non-empty string, minimum value, allowed enum values, nullable values, etc.).
- Whether the value is only display metadata, setup-time data, or must affect gameplay rules.

Use this distinction to decide how far the property must travel:

| Property purpose | Runtime/domain object update? | Typical API source |
| --- | --- | --- |
| Display-only scenario metadata | Usually no; keep it on scenario definitions unless runtime code also needs it. | Scenario object attached to the game response, scenario list metadata, or frontend mock data. |
| Setup-time input that changes initial board/game creation | Maybe; apply it during game creation, but only persist it on runtime objects if later rules or responses need it. | Scenario object during game creation and any resulting runtime state. |
| Gameplay rule/state property used after creation | Yes; add it to the relevant runtime object or rule service as well as scenario definitions. | Runtime game, board, unit, terrain, objective, movement, or combat objects, sometimes supplemented by scenario metadata. |

### 2. Add the property to scenario JSON files

Update the relevant scenario files in `battle_hexes_core/src/battle_hexes_core/scenarios/`.

Recommendations:

- Add the property to at least one scenario that exercises the new behavior.
- If the field is required, update every existing scenario file.
- If the field is optional, leave some existing scenarios without it and add loader tests proving the default behavior.
- Keep values representative enough to test frontend rendering or rules effects.

### 3. Update core scenario dataclasses

Edit `battle_hexes_core/src/battle_hexes_core/scenario/scenario.py` and add the property to the matching dataclass.

Common targets:

| JSON location | Core dataclass |
| --- | --- |
| Top-level scenario metadata | `Scenario` |
| `victory` | `ScenarioVictory` |
| `defensive_fire` | `DefensiveFireConfig` |
| `factions[]` | `ScenarioFaction` |
| `units[]` | `ScenarioUnit` |
| `terrain_types.*` | `ScenarioTerrainType` |
| `road_types.*` | `ScenarioRoadType` |
| `roads[]` | `ScenarioRoad` |
| `hex_data[]` | `ScenarioHexData` |
| `objectives[]` | Usually `battle_hexes_core.game.objective.Objective` |

Guidance:

- Put optional/defaulted fields after required fields.
- Prefer immutable/simple values because these dataclasses are frozen where currently defined.
- Use a default compatible with existing scenarios if the field is optional.
- If the value belongs to game runtime state rather than scenario definition only, also update the corresponding domain class (for example `Terrain`, `Unit`, `Objective`, `Board`, or `Game`).

### 4. Update scenario loader validation and conversion

Edit `battle_hexes_core/src/battle_hexes_core/scenario/scenario_loader.py`.

For the matching Pydantic validation model:

- Add a field with the same JSON name.
- Choose an appropriate type and validation constraints.
- Use defaults for backwards-compatible optional fields.
- Use strict types when coercion would be surprising. Existing examples use `StrictInt` for fields like `combat_odds_shift` and `stacking_limit`.

Then update the conversion from loader data into core dataclasses:

- Add the property to `ScenarioData.to_core()` for top-level scenario fields.
- Add it to helper methods such as `_build_factions()`, `_build_units()`, `_build_terrain_types()`, `_build_road_types()`, `_build_roads()`, `_build_hex_entries()`, or `_build_objective_map()` depending on where the property lives.
- If the property affects board/game construction, trace from the resulting `Scenario` object into game creation code and apply it there too.

Add or update `battle_hexes_core/tests/scenario/test_scenario_loader.py` to cover:

- Parsing raw `ScenarioData`.
- Conversion to the core dataclass.
- Default behavior for missing/null values when applicable.
- Rejection of invalid values when validation matters.

### 5. Apply the property to runtime game objects if needed

Some scenario properties only need to be listed or displayed. Others must change the created game. If the property affects actual gameplay, find the core code that consumes `Scenario` and applies it to runtime objects.

Likely places to inspect:

- `battle_hexes_core/src/battle_hexes_core/gamecreator/gamecreator.py` for turning a `Scenario` into a `Game` and `Board`.
- `battle_hexes_core/src/battle_hexes_core/game/board.py` for board, terrain, road, stacking, and hex state.
- `battle_hexes_core/src/battle_hexes_core/game/hex.py` for per-hex state.
- `battle_hexes_core/src/battle_hexes_core/game/terrain.py` for runtime terrain properties.
- `battle_hexes_core/src/battle_hexes_core/unit/unit.py` for runtime unit properties.
- `battle_hexes_core/src/battle_hexes_core/game/objective.py` and `battle_hexes_core/src/battle_hexes_core/scoring/` for objective/scoring changes.
- `battle_hexes_core/src/battle_hexes_core/combat/`, `movement.py`, or `defensivefire/` for rule changes.

Update tests in the relevant core package area. Prefer observable behavior and public contracts over private helper assertions.

### 6. Update API schemas

Expose the new value through the API only after it exists in core data/runtime objects.

Common API schema targets:

| Data exposed to frontend | API files to inspect |
| --- | --- |
| Scenario list metadata from `/scenarios` | `battle_hexes_api/src/battle_hexes_api/schemas/scenario.py` |
| Created/fetched game payload from `/games` or `/games/{id}` | `battle_hexes_api/src/battle_hexes_api/schemas/game_model.py` and `battle_hexes_api/src/battle_hexes_api/main.py` |
| Board-level values | `battle_hexes_api/src/battle_hexes_api/schemas/board.py` |
| Faction values inside players | `battle_hexes_api/src/battle_hexes_api/schemas/player.py` and `battle_hexes_api/src/battle_hexes_api/schemas/faction.py` |
| Terrain values | `battle_hexes_api/src/battle_hexes_api/schemas/terrain.py` |
| Unit values | `battle_hexes_api/src/battle_hexes_api/schemas/unit.py` |
| Objective values | `battle_hexes_api/src/battle_hexes_api/schemas/objective.py` |
| Movement/combat response values | `battle_hexes_api/src/battle_hexes_api/schemas/movement.py`, `combat.py`, or `sparseboard.py` |
| Create-game request inputs | `battle_hexes_api/src/battle_hexes_api/schemas/create_game.py` |

Implementation notes:

- Add Pydantic fields to the schema that directly represents the data.
- Update `from_core()` / `from_*()` factory methods to populate the field.
- Update `to_core()` if the schema supports round-tripping back to a core type.
- If the frontend expects `camelCase` for a top-level game response field, update `_serialize_game()` in `battle_hexes_api/src/battle_hexes_api/main.py` to rename fields or add top-level aliases.
- Treat existing nested `snake_case` API fields as current-state compatibility, not as the target convention for new fields. Before choosing any API response name, check `specs/naming-casing-cleanup.md`: HTTP API JSON and frontend mocks should move toward canonical `camelCase`, even for nested scenario-backed fields.
- Decide whether the value appears in `/scenarios`, created game responses, fetched game responses, movement responses, combat responses, or all of them.

Update tests such as:

- `battle_hexes_api/tests/test_schemas.py`.
- `battle_hexes_api/tests/test_schemas_board.py`.
- `battle_hexes_api/tests/test_main.py` for route-level JSON shape.
- Any movement/combat schema tests if the property flows through those responses.

### 7. Update frontend service and game creation mapping

The HTTP service mostly passes JSON through unchanged, so most frontend work starts in `battle-hexes-web/src/model/game-creator.js`.

Update `GameCreator.createGame()` and the relevant private helper to read the API response field and instantiate JavaScript model objects with the new value.

Examples of existing mapping patterns:

- Top-level scenario/game metadata is extracted before constructing `Game`.
- Player faction metadata is parsed in `#getFactions()` and converted into `Faction` instances.
- Board terrain metadata is parsed in `#addTerrain()` and converted into `Terrain` instances.
- Units are parsed in `#addUnits()` and converted into `Unit` instances.
- Objectives are parsed in `#addObjectives()` and converted into `Objective` instances.
- Roads are parsed in `#addRoads()` and converted into `Road`/`RoadType` instances.

When accepting API data:

- Treat API JSON as an external/untrusted boundary and validate shape enough to avoid crashes.
- Once data is inside established model objects, avoid unnecessary defensive clutter.
- Preserve existing naming compatibility only when needed. Several current helpers accept both `snake_case` and `camelCase` because historical responses use both.

Update or add JavaScript tests under `battle-hexes-web/tests/model/`, especially `game-creator.test.js`, for the new mapping.

### 8. Update frontend model classes

If the property is meant to be used after game creation, update the appropriate frontend model class:

- `battle-hexes-web/src/model/game.js` for game/scenario-level metadata.
- `battle-hexes-web/src/model/board.js` for board-level state.
- `battle-hexes-web/src/model/hex.js` for per-hex values.
- `battle-hexes-web/src/model/terrain.js` for terrain type metadata.
- `battle-hexes-web/src/model/unit.js` for unit metadata/rules.
- `battle-hexes-web/src/model/objective.js` for objective metadata.
- `battle-hexes-web/src/model/road.js` for road metadata.

For new frontend model fields:

- Prefer idiomatic JavaScript getters using `get propertyName()` for new models or new model-style accessors in this project.
- Keep constructor defaults consistent with API/core defaults.
- Add unit tests for storage and observable behavior.

### 9. Update frontend rendering/UI/behavior

If the property should be visible or affect play on the frontend, update the code that consumes the relevant model:

- `battle-hexes-web/src/drawer/` for board, hex, terrain, unit, road, overlay, and selection visuals.
- `battle-hexes-web/src/terraindraw/` for terrain-specific drawing behavior.
- `battle-hexes-web/src/menu.js`, `title-screen*.js`, or `battle-draw.js` for UI or scenario selection displays.
- `battle-hexes-web/src/player/` for player behavior.
- `battle-hexes-web/src/model/combat-resolver.js`, `movement-response-handler.js`, or `board-updater.js` if the property must persist through server responses after actions.

Update frontend tests near the changed behavior. If the UI visibly changes, run the web build/tests and, when practical, use mock-service mode for a screenshot or manual check.

### 10. Update mock responses and fixtures

Keep test and development fixtures aligned with the real API shape:

- `battle-hexes-web/src/service/mock-responses/get-game.json`.
- `battle-hexes-web/src/service/mock-responses/move.json`.
- `battle_hexes_api/sample-game-data.json` if it represents the changed payload.
- Unit test fixtures in API and frontend test files.

Mocks should include at least one non-default value so frontend mapping tests can catch missing serialization.

### 11. Run checks

For a full end-to-end scenario property change, run as many of these as apply:

```bash
./server-side-checks.sh
```

```bash
cd battle-hexes-web && npm test
```

```bash
cd battle-hexes-web && npm run test-and-build
```

For focused iteration, run narrower tests first, such as:

```bash
PYTHONPATH="$PWD/battle_hexes_core/src:$PWD/battle_agent_rl/src:$PWD/battle_hexes_api/src" pytest battle_hexes_core/tests/scenario/test_scenario_loader.py
```

```bash
PYTHONPATH="$PWD/battle_hexes_core/src:$PWD/battle_agent_rl/src:$PWD/battle_hexes_api/src" pytest battle_hexes_api/tests/test_schemas.py battle_hexes_api/tests/test_schemas_board.py battle_hexes_api/tests/test_main.py
```

```bash
cd battle-hexes-web && npm test -- game-creator.test.js
```

## Worked Example: Adding a New Terrain Type Property

Suppose a scenario terrain type adds `display_priority` and the frontend uses it to decide overlay order.

1. Add `display_priority` under a terrain entry in a scenario JSON file:

   ```json
   "terrain_types": {
     "village": {
       "color": "#9A8F7A",
       "move_cost": 2,
       "combat_odds_shift": -1,
       "display_priority": 20
     }
   }
   ```

2. Add `display_priority: int = 0` to `ScenarioTerrainType` in `scenario.py`.
3. Add `display_priority: StrictInt = 0` to `ScenarioTerrainTypeData` in `scenario_loader.py`.
4. Pass `display_priority=terrain_type.display_priority` inside `_build_terrain_types()`.
5. Add loader tests proving the value is parsed, converted, defaults to zero, and rejects non-integers if strict typing is desired.
6. Add `display_priority` to `TerrainTypeModel` in `battle_hexes_api/src/battle_hexes_api/schemas/terrain.py` and populate it in `from_scenario_type()`.
7. Add API schema/route tests proving the game response includes `board.terrain.types.village.display_priority`.
8. Update `battle-hexes-web/src/model/terrain.js` constructor and getter.
9. Update `battle-hexes-web/src/model/game-creator.js` `#addTerrain()` to pass `value.display_priority` into `new Terrain(...)`.
10. Update frontend tests in `game-creator.test.js` and `terrain.test.js`.
11. Update drawers/overlay code to sort or render by `terrain.displayPriority`.

    Because this example property only controls frontend rendering order, it can remain scenario/API/frontend metadata and does not need to be added to the core runtime `Terrain` class unless backend rules also consume it.

12. Add the new property to mock responses.
13. Run backend and frontend checks.

## Common Pitfalls

- **Only updating JSON and frontend code.** The property will be rejected or dropped unless it is added to `ScenarioData`, converted to core dataclasses, and serialized by API schemas.
- **Adding core data but not applying it to runtime objects.** The property may exist on `Scenario` but never affect the `Game`, `Board`, `Terrain`, `Unit`, or `Objective` objects used during play.
- **Forgetting API naming conventions.** Python fields are often `snake_case`, while selected frontend-facing fields are `camelCase` after `_serialize_game()`.
- **Updating `/scenarios` but not `/games`.** Scenario list cards and active game payloads are different API shapes.
- **Updating created games but not fetched games.** The same serializer should usually support both `/games` and `/games/{id}`.
- **Forgetting movement/combat responses.** If a property changes during play or must persist after an action, make sure movement, combat, sparse-board schemas, and frontend response handlers carry it forward.
- **Leaving mock-service responses stale.** Web tests or mock builds may still pass old data unless fixtures are updated.
- **Testing implementation details instead of behavior.** Prefer tests that prove the value is visible in core objects, API JSON, and frontend models/behavior.
