# Battle Hexes Web: Centralized Backend Boundary via BattleHexesService

## Goal

Refactor the Battle Hexes web frontend to depend on a single service abstraction
instead of calling the backend directly via `fetch` and `axios`.

Create:

- `BattleHexesService` (interface / contract)
- `HttpBattleHexesService` (real implementation using HTTP)
- `MockBattleHexesService` (offline implementation; returns safe placeholder data)

This enables running the web project in an **offline/mock mode** without the
backend, while keeping the rest of the app agnostic to URLs and HTTP details.

---

## Motivation / Current State

The following files currently call the backend directly (mix of `fetch` and
`axios`):

- `battle-hexes-web/src/model/game.js`
- `battle-hexes-web/src/model/combat-resolver.js`
- `battle-hexes-web/src/battle-draw.js`
- `battle-hexes-web/src/menu.js`
- `battle-hexes-web/src/player/cpu-player.js`
- `battle-hexes-web/src/title-screen.js`
- `battle-hexes-web/src/title-screen-scenarios.js`
- `battle-hexes-web/src/title-screen-player-types.js`

We want to centralize the boundary first, so:
- All backend endpoints / URLs / HTTP concerns live in one place.
- The rest of the app depends only on `BattleHexesService`.
- Switching between real backend and mock backend is a runtime/build-time toggle.

---

## Non-Goals (for this change)

- Implement full mock gameplay logic.
- Rework backend API contracts.
- Remove `axios` from the bundle entirely. It is acceptable for the HTTP service
  to use either `axios` or `fetch` internally.
- Redesign the UI for empty/mock states beyond what is needed to avoid crashes.
- Perfect error handling/UX (basic parity is enough).

---

## Service Contract

### Location

Add new service files under a dedicated folder, for example:

- `battle-hexes-web/src/service/battle-hexes-service.js`
- `battle-hexes-web/src/service/http-battle-hexes-service.js`
- `battle-hexes-web/src/service/mock-battle-hexes-service.js`
- `battle-hexes-web/src/service/service-factory.js`

> Naming and folder layout can be adjusted, but keep a single obvious place
> for the boundary.

### Interface: `BattleHexesService`

Define a JS “interface” as a documented contract (JSDoc + runtime shape),
implemented by both concrete services.

All methods return `Promise<...>`.

#### Methods

- `listScenarios()`
- `listPlayerTypes()`
- `createGame(config)`
- `getGame(gameId)`
- `resolveHumanMove(gameId, sparseBoard)`
- `generateCpuMovement(gameId)`
- `resolveCombat(gameId, sparseBoard)`
- `endMovement(gameId, sparseBoard)`
- `endTurn(gameId, sparseBoard)`

> Use method names that match the current product behavior. In particular,
> there are **two distinct movement endpoints** today:
> - human incremental movement: `POST /games/{gameId}/move`
> - CPU movement generation: `POST /games/{gameId}/movement`
>
> Do not collapse these into one ambiguous `resolveMovement()` method.

### Data Shapes (must match current callers)

The service should preserve the backend payload shapes that the existing UI code
already expects, rather than inventing a new shape.

- `listScenarios()` returns the current `/scenarios` array payload.
  - Each item should at minimum preserve `id`, `name`, `description`, and
    `victory` when present.
- `listPlayerTypes()` returns the current `/player-types` array payload.
  - Each item should at minimum preserve `id` and `name`.
- `createGame(config)` returns the full serialized game payload returned by
  `POST /games`.
  - Important: current callers expect `response.id`, **not** `{ gameId }`.
- `getGame(gameId)` returns the same serialized game payload returned by
  `GET /games/{gameId}`.
- `resolveHumanMove(gameId, sparseBoard)` returns the movement response payload
  currently returned by `POST /games/{gameId}/move`.
- `generateCpuMovement(gameId)` returns the movement response payload currently
  returned by `POST /games/{gameId}/movement`.
- `endMovement(gameId, sparseBoard)` returns the movement response payload
  currently returned by `POST /games/{gameId}/end-movement`.
- `resolveCombat(gameId, sparseBoard)` returns the sparse-board-style payload
  currently returned by `POST /games/{gameId}/combat`.
- `endTurn(gameId, sparseBoard)` returns the payload currently returned by
  `POST /games/{gameId}/end-turn`.

> During implementation, align these return shapes with what the calling code
> currently uses. Prefer minimal adjustments to callers, and adapt in the
> service layer where possible.

---

## HttpBattleHexesService

### Purpose

Encapsulate all HTTP calls, URL building, headers, and error translation.

### Requirements

- Accept an `apiBaseUrl` (for example from webpack env config).
- Use either `axios` or `fetch` internally, but **no other code** should call
  `axios` or `fetch` for backend endpoints after the refactor.
- Provide a clear mapping from each service method to its backend endpoint.
- Keep JSON serialization details inside this class.

### Endpoint Mapping

Map methods to the backend exactly as it exists today:

- `listScenarios()` -> `GET /scenarios`
- `listPlayerTypes()` -> `GET /player-types`
- `createGame(config)` -> `POST /games`
- `getGame(gameId)` -> `GET /games/{gameId}`
- `resolveHumanMove(gameId, sparseBoard)` -> `POST /games/{gameId}/move`
- `generateCpuMovement(gameId)` -> `POST /games/{gameId}/movement`
- `resolveCombat(gameId, sparseBoard)` -> `POST /games/{gameId}/combat`
- `endMovement(gameId, sparseBoard)` -> `POST /games/{gameId}/end-movement`
- `endTurn(gameId, sparseBoard)` -> `POST /games/{gameId}/end-turn`

### Example Responsibilities

- Convert JS objects to JSON request bodies.
- Parse JSON responses.
- Normalize errors (at least log + throw).
- Optionally expose small helper methods for `GET`/`POST` to avoid repetition.

---

## MockBattleHexesService

### Purpose

Enable “frontend without backend” mode.

### Requirements (initial)

- Implements the full `BattleHexesService` contract.
- Returns valid Promises.
- Returns placeholder data that lets the title screen and battle screen fail
  gracefully instead of crashing.

### Important behavior constraints

The current UI does **not** safely support arbitrary `{}` responses everywhere.
The mock service should therefore return payloads with the minimum fields needed
by existing callers.

At minimum:

- `listScenarios()` should return either `[]` or a small fixture list.
- `listPlayerTypes()` should return either `[]` or a small fixture list.
- `createGame(config)` must return an object with an `id` field.
  - Example: `{ id: "mock-game" }`
- `getGame(gameId)` should return either:
  - a fixture game payload shaped like the real backend response, or
  - if that is too much for this change, the spec should be implemented together
    with defensive UI handling so mock mode does not boot directly into a broken
    battle screen.
- `resolveHumanMove(...)`, `generateCpuMovement(...)`, and `endMovement(...)`
  should return a movement-style payload containing the fields the callers read
  today (`plans`, `sparse_board` and/or `game`, plus score/turn fields when
  needed).
- `resolveCombat(...)` should return a payload compatible with current combat
  handling (`units` and `last_combat_results` are the most likely required
  fields).
- `endTurn(...)` should return at least score/turn metadata if the UI continues
  to read it.

> Follow-up enhancements can add richer fixtures and/or in-memory state. For
> this PR, the priority is creating the seam and ensuring mock mode is explicit
> about any limited behavior.

---

## Service Selection (Real vs Mock)

### Requirement

Add a single selection mechanism so developers can run the frontend in either:

- **Real mode**: uses `HttpBattleHexesService` (requires backend)
- **Mock mode**: uses `MockBattleHexesService` (no backend required)

### Standard Approach

Use webpack env variables wired through the frontend build:

- `BATTLE_HEXES_SERVICE_MODE=mock|http`
- `API_URL=http://localhost:8000`

### Important implementation detail

The current webpack config only injects `process.env.API_URL`.
This refactor must also inject `process.env.BATTLE_HEXES_SERVICE_MODE`
(otherwise the new toggle will not work in the bundled frontend).

### Implementation Options

**Option A (recommended): Service Factory**

Create `battle-hexes-web/src/service/service-factory.js`:

- Reads `process.env.BATTLE_HEXES_SERVICE_MODE`
- If `mock`, returns `new MockBattleHexesService()`
- Else returns `new HttpBattleHexesService({ apiBaseUrl: process.env.API_URL })`

### Where the service instance lives

- Create **one** service instance per page load.
- Export the singleton from the factory module and import it where needed.
- Prefer passing the service into helper initializers where that keeps tests
  simple, rather than threading raw `fetchImpl` / `apiUrl` values through UI
  modules.

---

## Refactor Plan (Call Site Updates)

### Target Files (replace direct HTTP calls)

- `battle-hexes-web/src/model/game.js`
- `battle-hexes-web/src/model/combat-resolver.js`
- `battle-hexes-web/src/battle-draw.js`
- `battle-hexes-web/src/menu.js`
- `battle-hexes-web/src/player/cpu-player.js`
- `battle-hexes-web/src/title-screen.js`
- `battle-hexes-web/src/title-screen-scenarios.js`
- `battle-hexes-web/src/title-screen-player-types.js`

### Rules

- These modules must no longer import `axios` or call `fetch` for backend work.
- URL strings and endpoint paths must move into `HttpBattleHexesService`.
- `battle-hexes-web/src/model/battle-api.js` should be removed or reduced to a
  compatibility shim only if still needed temporarily.

### Migration Strategy

1. Create the service contract + both implementations.
2. Introduce the selection mechanism and export a singleton service instance.
3. Update each file to use the service for backend interactions.
4. Ensure both modes build/run:
   - `http` mode should behave like today.
   - `mock` mode should load without requiring the backend.
5. Update/add unit tests for the touched frontend modules.

---

## Running the Web Project

### Real / HTTP Mode (backend required)

Example:

```bash
BATTLE_HEXES_SERVICE_MODE=http \
API_URL=http://localhost:8000 \
npm run dev
```

### Mock Mode (backend not required)

Example:

```bash
BATTLE_HEXES_SERVICE_MODE=mock \
API_URL=http://localhost:8000 \
npm run dev
```

`API_URL` may still be provided in mock mode for convenience, but it should not
be used by `MockBattleHexesService`.

---

## Acceptance Criteria

- There is one clearly documented frontend service boundary for backend access.
- Direct backend `fetch`/`axios` calls are removed from the target modules.
- The service contract distinguishes human move resolution from CPU movement
  generation.
- `createGame()` and the other methods preserve the response shapes that the UI
  currently relies on.
- `BATTLE_HEXES_SERVICE_MODE` is wired into the frontend build configuration.
- `http` mode keeps existing behavior.
- `mock` mode can be launched intentionally and does not immediately crash due
  to obviously malformed placeholder responses.
