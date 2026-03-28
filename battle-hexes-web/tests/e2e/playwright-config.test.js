const path = require('path');
const config = require('../../playwright.config.js');

describe('playwright configuration', () => {
  test('serves the mock build over HTTP without backend dependency', () => {
    expect(config.use.baseURL).toBe('http://127.0.0.1:4173');
    expect(config.webServer.url).toBe('http://127.0.0.1:4173');

    expect(config.webServer.command).toContain('npm run build:mock');
    expect(config.webServer.command).toContain('python -m http.server 4173 --directory dist');
    expect(config.webServer.command).not.toContain('uvicorn');

    expect(config.webServer.cwd).toBe(path.join(__dirname, '..', '..'));
  });
});
