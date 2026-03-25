# AGENTS.md — Battle Hexes Web

When making code changes in this web project, run the following to ensure the build and tests are successfull:

```bash
npm run test-and-build
```

When validating changes that do not require a live backend (especially screen shots), prefer the offline mock-service mode:

```bash
npm run build:mock
```

Do not assume the backend is running for normal web-only changes. If a task explicitly depends on real backend behavior, say so and use the appropriate backend-connected workflow for that case.

## General Advice
Add or update unit tests to cover your changes.

When adding new models, use idiomatic JavaScript getters (the `get` keyword)
instead of Java-like `getX()` methods.

For open terrain rendering, use `aHex.hexSeed` directly for deterministic randomness; avoid fallback/defensive seed derivation logic unless explicitly requested.

Assume normal internal application invariants hold. Avoid defensive JavaScript clutter such as existence checks, optional chaining, fallback defaults, and `typeof ... === 'function'` guards for established internal objects unless the value is truly optional or comes from an external/untrusted boundary.
