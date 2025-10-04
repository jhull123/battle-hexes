# Battle Hexes Web

Web based UI for the Battle Hexes game.

## Commands

### Linting

    npm run lint

### Running Tests

    npm test

### Running Integration Tests

The web frontend now includes simple browser-based tests using Playwright.

    # Install Playwright browsers if you haven't already
    npx playwright install
    
    npm run test:e2e

### Building the App

Build for a locally running API:

    npm run build

Build for the dev API deployment:

    npm run build:dev

After building, open `dist/index.html` to view the title screen. The game board
is now served from `dist/battle.html`, which you can reach via the "Enter
Battle" button on the landing page or by navigating directly to the file.

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

