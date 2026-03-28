const path = require('path');

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: path.join(__dirname, 'e2e'),
  timeout: 30_000,
  use: {
    baseURL: 'http://127.0.0.1:4173',
  },
  webServer: {
    command: 'npm run build:mock && python -m http.server 4173 --directory dist',
    url: 'http://127.0.0.1:4173',
    cwd: __dirname,
    reuseExistingServer: !process.env.CI,
  },
};

module.exports = config;
