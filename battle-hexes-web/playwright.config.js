const path = require('path');

/** @type {import('@playwright/test').PlaywrightTestConfig} */
const config = {
  testDir: path.join(__dirname, 'e2e'),
  timeout: 30_000,
  webServer: {
    command: 'python -m uvicorn src.main:app --port 8000',
    port: 8000,
    cwd: path.join(__dirname, '..', 'battle_hexes_api'),
    reuseExistingServer: !process.env.CI,
  },
};

module.exports = config;
