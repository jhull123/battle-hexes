# Battle Hexes Web: Centralized Backend Boundary via BattleHexesService

## Goal

Refactor the Battle Hexes web frontend to depend on a single service abstraction
instead of calling the backend directly via `fetch` and `axios`.

Create:

- `BattleHexesService` (interface / contract)
- `HttpBattleHexesService` (real implementation using HTTP)
- `MockBattleHexesService` (offline implementation; returns empty data for now)

This enables running the web project in an **offline/mock mode** without the
backend, while keeping the rest of the app agnostic to URLs and HTTP details.

---

## Motivation / Current State

The following files currently call the backend directly (mix of `fetch` and
`axios`), which makes “run the frontend without the backend” possible but
awkward and scattered:

- `battle-hexes-web/src/model/game.js`
- `battle-hexes-web/src/battle-draw.js`
- `battle-hexes-web/src/menu.js`
- `battle-hexes-web/src/player/cpu-player.js`
- `battle-hexes-web/src/title-screen*.js`

We want to centralize the boundary first, so:
- All backend endpoints / URLs / HTTP concerns live in one place.
- The rest of the app depends only on `BattleHexesService`.
- Switching between real backend and mock backend is a runtime/build-time toggle.

---

## Non-Goals (for this change)

- Implement full mock gameplay logic.
- Rework backend API contracts.
- Replace axios everywhere (the HTTP service may use axios or fetch).
- Perfect error handling/UX (basic parity is enough).

---

## Service Contract

### Location

Add new service files under a dedicated folder, for example:

- `battle-hexes-web/src/service/battle-hexes-service.js`
- `battle-hexes-web/src/service/http-battle-hexes-service.js`
- `battle-hexes-web/src/service/mock-battle-hexes-service.js`
- `battle-hexes-web/src/service/service-factory.js` (optional but recommended)

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
- `resolveMovement(gameId, sparseBoard)`
- `resolveCombat(gameId, sparseBoard)`
- `runCpuMovement(gameId)`
- `endMovement(gameId, sparseBoard)`
- `endTurn(gameId, sparseBoard)`

#### Data Shapes (Minimum Expectations)

This spec intentionally allows “empty data” for mocks, but we still define the
minimum shapes so the UI can be wired consistently.

- `listScenarios()` returns an array:
  - `[]` initially is acceptable in mock mode.
- `listPlayerTypes()` returns an array:
  - `[]` initially is acceptable in mock mode.
- `createGame(config)` returns:
  - `{ gameId: string }` (or whatever the UI expects today)
  - mock may return `{ gameId: "mock-game" }`
- `getGame(gameId)` returns:
  - a `game` object (can be empty `{}` in mock for now)
- `resolveMovement/resolveCombat/endMovement/endTurn(...)` return:
  - an updated `game` object or a result payload consistent with existing code
  - mock may return `{}` initially
- `runCpuMovement(gameId)` returns:
  - updated `game` or action result payload
  - mock may return `{}` initially

> During implementation, align these return shapes with what the calling code
> currently uses. Prefer minimal adjustments to callers, and adapt in the
> service layer where possible.

---

## HttpBattleHexesService

### Purpose

Encapsulate all HTTP calls, URL building, headers, and error translation.

### Requirements

- Accept an `apiBaseUrl` (e.g., from environment/build config).
- Use either `axios` or `fetch` internally, but **no other code** should call
  `axios` or `fetch` for backend endpoints after refactor.
- Provide clear mapping from each service method to its backend endpoint(s).

### Example Responsibilities

- Convert JS objects to JSON request bodies.
- Parse JSON responses.
- Normalize errors (at least log + throw).

---

## MockBattleHexesService

### Purpose

Enable “frontend without backend” mode.

### Requirements (initial)

- Implements the full `BattleHexesService` contract.
- Returns valid Promises.
- Returns **empty data** that won’t crash the UI where feasible.

### Initial Return Behavior (acceptable for this PR)

- `listScenarios()` -> `Promise.resolve([])`
- `listPlayerTypes()` -> `Promise.resolve([])`
- `createGame(config)` -> `Promise.resolve({ gameId: "mock-game" })`
- `getGame(gameId)` -> `Promise.resolve({})`
- All other methods -> `Promise.resolve({})`

> Follow-up enhancements can add fixtures and/or in-memory state. For now, the
> goal is to create the seam and the selection mechanism.

---

## Service Selection (Real vs Mock)

### Requirement

Add a single selection mechanism so developers can run the frontend in either:

- **Real mode**: uses `HttpBattleHexesService` (requires backend)
- **Mock mode**: uses `MockBattleHexesService` (no backend required)

### Standard Approach

Use an environment variable wired through the frontend build:

- `BATTLE_HEXES_SERVICE_MODE=mock|http`

And optionally:
- `API_URL=http://localhost:8000` (existing pattern)

### Implementation Options

**Option A (recommended): Service Factory**

Create `battle-hexes-web/src/service/service-factory.js`:

- Reads `process.env.BATTLE_HEXES_SERVICE_MODE`
- If `mock`, returns `new MockBattleHexesService()`
- Else returns `new HttpBattleHexesService({ apiBaseUrl: process.env.API_URL })`

**Option B: Simple conditional in a shared module**

In a single `battle-hexes-service.js` export `getBattleHexesService()` that
selects the implementation.

### Where the service instance lives

- Create **one** service instance per page load.
- Export the singleton from the factory module and import it where needed.

---

## Refactor Plan (Call Site Updates)

### Target Files (replace direct HTTP calls)

- `battle-hexes-web/src/model/game.js`
- `battle-hexes-web/src/battle-draw.js`
- `battle-hexes-web/src/menu.js`
- `battle-hexes-web/src/player/cpu-player.js`
- `battle-hexes-web/src/title-screen*.js`

### Rules

- These modules must no longer import `axios` or call `fetch` for backend work.
- They must call the service methods listed in the contract.
- URL strings and endpoint paths should move into `HttpBattleHexesService`.

### Migration Strategy

1. Create the service interface + both implementations (mock can be stubby).
2. Introduce selection mechanism and export a singleton instance.
3. Update each file to use the singleton service for its backend interactions.
4. Ensure both modes build/run:
   - `http` mode should behave like today.
   - `mock` mode should start without backend (UI may be limited due to empty data).

---

## Running the Web Project

### Real / HTTP Mode (backend required)

Example (Webpack env pattern already exists in project):

```bash
BATTLE_HEXES_SERVICE_MODE=http \
API_URL=http://localhost:8000 \
npm run dev