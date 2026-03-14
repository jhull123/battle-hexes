# AGENTS.md — Battle Hexes Web

When making code changes in this web project, run:

```
npm run test-and-build
```

Add or update unit tests to cover your changes.

When adding new models, use idiomatic JavaScript getters (the `get` keyword)
instead of Java-like `getX()` methods.

For open terrain rendering, use `aHex.hexSeed` directly for deterministic randomness; avoid fallback/defensive seed derivation logic unless explicitly requested.
