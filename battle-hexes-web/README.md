# Battle Hexes Web

Web based UI for the Battle Hexes game.

## Commands

### Linting

    npm run lint

### Running Tests

    npm test

### Running Integration Tests (Playwright E2E)

Playwright tests live in `battle-hexes-web/e2e` and run against the built frontend in **mock-service mode**.

`npm run test:e2e` uses `playwright.config.js` to:
- build the app with `npm run build:mock`, and
- serve `dist/` over `http://127.0.0.1:4173`.

This means e2e tests do **not** require `battle_hexes_api` / `uvicorn`.

    # Install Playwright browser binaries
    npx playwright install

    # Run e2e tests (build + local HTTP server are handled by Playwright config)
    npm run test:e2e

If the browser install succeeds but test launch fails on Linux with missing system libraries, run:

    npx playwright install-deps

Or install the required packages with apt (example):

    apt-get install libatk1.0-0t64 libatk-bridge2.0-0t64 libatspi2.0-0t64 \
      libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libxkbcommon0 \
      libasound2t64

### Building the App

Build for a locally running API:

    npm run build

Build for the dev API deployment:

    npm run build:dev

After building, open `dist/index.html` to view the title screen. The game board
is now served from `dist/battle.html`, which you can reach via the "Enter
Battle" button on the landing page or by navigating directly to the file.

### Service Modes (HTTP vs Mock)

The frontend supports two backend service modes:

- `http` (default): uses `HttpBattleHexesService` and calls the backend API.
- `mock`: uses `MockBattleHexesService` and returns local placeholder payloads
  so you can run the UI without a backend.

`API_URL` is used by `http` mode. It can still be set in `mock` mode for
convenience, but mock mode does not call the backend.

Run with the real backend (http://localhost:8000):

    npm run build

Run offline with the mock service:

    npm run build:mock

Or:

    npm run build -- --env BATTLE_HEXES_SERVICE_MODE=mock

### Optional HTTP Response Logging Mode

When using `HttpBattleHexesService`, you can enable console logging for server
responses at build time:

    npm run build -- --env LOG_SERVER_RESPONSES=true

When enabled, the service logs each successful JSON response in this format:

    server response for [methodName]: [json as text]

### Lint, Test, and Build

    npm run test-and-build

## Deployment

The `cloudformation-template.yml` provisions an S3 bucket, CloudFront
distribution, and Route 53 record for a custom domain. You will need:

- `BucketName` – S3 bucket for static assets
- `AcmCertificateArn` – ACM certificate ARN in `us-east-1`
- `HostedZoneId` – Route 53 hosted zone ID for `battlehexes.com`
- `WebDomainName` – (optional) fully qualified domain name, defaults to
  `dev.battlehexes.com`

Deploy using AWS CLI:

```
aws cloudformation deploy \
  --template-file cloudformation-template.yml \
  --stack-name battle-hexes-web \
  --parameter-overrides BucketName=YOUR_BUCKET \
    AcmCertificateArn=YOUR_CERT_ARN HostedZoneId=YOUR_ZONE_ID \
    WebDomainName=dev.battlehexes.com
```

After the stack completes, the site will be served from your specified
domain using HTTPS.
