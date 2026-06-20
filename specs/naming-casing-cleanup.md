# Naming Casing Cleanup Specification

## Purpose

Battle Hexes currently exposes a mix of `snake_case` and `camelCase` names across
scenario JSON, Python internals, API payloads, and JavaScript internals. This
spec describes how to clean up that naming split while preserving idiomatic code
at each layer and minimizing compatibility risk.

## Goals

- Use idiomatic names within each language/runtime boundary:
  - Python code and Pydantic model attributes use `snake_case`.
  - JavaScript code, frontend model properties, and frontend method parameters
    use `camelCase`.
  - Scenario authoring JSON remains `snake_case` because it is loaded directly
    by the Python core package and closely mirrors Python domain concepts.
  - HTTP API request and response JSON uses `camelCase` because it is consumed
    by the JavaScript frontend and is the client-facing contract.
- Remove ad hoc casing conversions from scattered route and frontend mapping
  code.
- Keep backwards-compatible read support for existing `snake_case` API payloads
  only during a documented migration window.
- Make mock responses, sample payloads, and tests enforce the chosen casing.

## Non-Goals

- Do not rename Python attributes, core dataclasses, or scenario loader fields to
  `camelCase`.
- Do not rename JavaScript variables, methods, or model accessors to
  `snake_case`.
- Do not change the scenario JSON casing unless the project later decides that
  scenario files are also a public web-facing format.
- Do not redesign API resources beyond naming normalization.

## Current State

The current API contract is inconsistent:

- Some top-level game response fields are manually converted to `camelCase`, such
  as `scenarioId`, `scenarioName`, `stackingLimit`, `turnLimit`, `turnNumber`,
  and `playerTypeIds`.
- Some request models already use Pydantic aliases to accept `camelCase`, such as
  `scenarioId` and `playerTypes` for game creation.
- Several nested response fields remain `snake_case`, such as terrain
  `move_cost`, terrain `combat_odds_shift`, board `road_types`, and board
  `road_paths`.
- Frontend mapping code accepts both styles for some top-level fields but expects
  `snake_case` for several nested objects.
- Mock responses contain the same mixture, which makes it hard to tell whether a
  new field should be added as `snake_case`, `camelCase`, or both.

This inconsistency is understandable historically, but it increases the chance
that new end-to-end scenario properties are serialized with the wrong casing or
that tests accidentally bless both names forever.

## Target Casing Policy

| Layer | Casing | Rationale |
| --- | --- | --- |
| Scenario JSON under `battle_hexes_core/src/battle_hexes_core/scenarios/` | `snake_case` | Authored for the Python core loader and aligned with Python schema names. |
| Python core/domain code | `snake_case` | Idiomatic Python and already used by dataclasses, methods, and attributes. |
| Python Pydantic model attributes | `snake_case` | Keeps Python code idiomatic and avoids leaking JSON naming into internals. |
| HTTP API JSON requests | `camelCase` | Client-facing JSON consumed by the JavaScript frontend. |
| HTTP API JSON responses | `camelCase` | Client-facing JSON consumed by the JavaScript frontend. |
| JavaScript model/service/UI code | `camelCase` | Idiomatic JavaScript and already used by frontend classes. |
| Frontend mock responses | `camelCase` | They should represent the HTTP API contract, not Python internals. |
| API sample payloads | `camelCase` | They should represent the HTTP API contract. |

## API Serialization Design

### Pydantic Alias Strategy

API schemas should use `snake_case` Python attributes with `camelCase` JSON
aliases. Prefer a shared alias strategy instead of hand-written conversions in
routes.

Recommended approach:

1. Add a shared API schema base class, for example `ApiBaseModel`, in the API
   schemas package.
2. Configure it with a snake-to-camel alias generator and `populate_by_name=True`.
3. Use `model_dump(by_alias=True)` for route responses.
4. Use explicit aliases only when a field does not follow mechanical
   snake-to-camel conversion or when a compatibility exception is unavoidable.

Example intent, not final code:

```python
class ApiBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

This lets Python code use `turn_number` while API JSON emits `turnNumber`.

### Route Serialization

Routes should not manually rename ordinary fields after dumping models. Manual
route-level additions should be limited to values that are not actually part of
that schema or temporary compatibility fields that have a removal plan.

Target behavior:

- Replace route-level `model["turnLimit"] = model.pop("turn_limit", None)` style
  conversions with schema aliases.
- Move top-level additions such as `scenarioId`, `scenarioName`,
  `stackingLimit`, and `playerTypeIds` into explicit schema fields when they are
  part of the game response contract.
- Ensure created-game and fetched-game responses use the same response schema and
  casing.
- Ensure movement, combat, end-turn, and sparse-board responses use aliases when
  returned to the frontend.

### Request Parsing

Client-facing request schemas should accept `camelCase` as the canonical input.
During migration, request schemas may also accept `snake_case` via
`populate_by_name=True`, but tests should emphasize `camelCase` as the supported
contract.

## Frontend Design

Frontend code should treat API JSON as `camelCase` at the service boundary.

Target behavior:

- `GameCreator` and other response mappers should prefer `camelCase` field reads.
- Temporary fallbacks for `snake_case` should be isolated in clearly named
  compatibility helpers.
- Frontend model constructors and getters should remain `camelCase`.
- Once the backend emits only `camelCase` and mocks are updated, remove
  compatibility reads for old nested `snake_case` response fields.

Examples of frontend API field changes:

| Current API field | Target API field |
| --- | --- |
| `board.terrain.types.*.move_cost` | `board.terrain.types.*.moveCost` |
| `board.terrain.types.*.combat_odds_shift` | `board.terrain.types.*.combatOddsShift` |
| `board.road_types` | `board.roadTypes` |
| `board.road_paths` | `board.roadPaths` |
| `turn_number` in nested action payloads | `turnNumber` |

## Scenario JSON Design

Scenario JSON should remain `snake_case` for now. It is not the same contract as
HTTP API JSON:

- Scenario files are part of the Python/core authoring path.
- Existing scenario loader models already use `snake_case` field names.
- Keeping scenario JSON in `snake_case` avoids needless churn in all scenario
  files and core loader tests.

If scenario JSON later becomes a public browser-authored format, create a
separate spec to decide whether scenario authoring should also move to
`camelCase` or support aliases.

## Migration Plan

### Phase 1: Inventory and Tests

- Inventory every API request and response schema field.
- Add API route tests that assert canonical `camelCase` response keys for game,
  scenario list, movement, combat, end-turn, and sparse-board payloads.
- Add frontend service/model tests that use canonical `camelCase` mock payloads.
- Add regression tests proving scenario JSON remains accepted as `snake_case`.

### Phase 2: Shared API Alias Infrastructure

- Introduce the shared API base model with snake-to-camel aliases.
- Convert schemas incrementally to inherit from the shared base.
- Update route serialization to call `model_dump(by_alias=True)`.
- Keep temporary read compatibility for old `snake_case` API payloads where the
  frontend still needs it.

### Phase 3: Payload and Mock Conversion

- Convert frontend mock responses and API sample payloads to canonical
  `camelCase` API JSON.
- Update frontend mappers to read canonical `camelCase` fields first.
- Keep fallback reads only for a short, documented compatibility period.

### Phase 4: Compatibility Removal

- Remove frontend fallback reads for obsolete `snake_case` API response fields.
- Remove route-level manual casing conversions that are superseded by schema
  aliases.
- Remove tests that intentionally accept both casing styles for API responses,
  except where backwards compatibility is explicitly required.

## Validation Strategy

- Run Python API schema and route tests after each schema conversion.
- Run frontend model/service tests after mock payload updates.
- Run full server-side checks and frontend tests before removing compatibility
  shims.
- Review generated or sample payloads manually to ensure no mixed casing remains
  within the HTTP API JSON contract.

## Risks and Mitigations

- **Risk: breaking existing clients that consume `snake_case` API response
  fields.** Mitigate by using a migration window with frontend compatibility
  reads and a clear removal commit.
- **Risk: accidental scenario JSON churn.** Mitigate by explicitly excluding
  scenario files from the API JSON casing migration.
- **Risk: overusing explicit aliases.** Mitigate by using a shared alias
  generator and reserving explicit aliases for non-mechanical names.
- **Risk: inconsistent mocks.** Mitigate by converting mock responses and sample
  payloads in the same phase as frontend mapper updates.

## Open Questions

1. Are there any external clients beyond the bundled web frontend that currently
   depend on `snake_case` API response fields?
   ANSWER: No
2. Should `/scenarios` responses also become fully `camelCase`, or should they
   continue to mirror scenario JSON more closely because they describe authoring
   metadata?
   ANSWER: Anything coming from the API, including scenario data, must be `camelCase`.
3. What compatibility window is acceptable before removing frontend reads for old
   `snake_case` API response fields?
   ANSWER: No compabibility window is needed.

