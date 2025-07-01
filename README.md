# battle-hexes
Turn-based strategy game engine.

## Integration Tests

The web frontend now includes simple browser-based tests using Playwright.
Install npm dependencies and run:

```bash
cd battle-hexes-web
npm run test:e2e
```

The command builds the frontend, starts the API with Uvicorn, and runs the
Playwright test suite.
