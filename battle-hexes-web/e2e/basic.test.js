import { test, expect } from '@playwright/test';
import path from 'path';

const indexPath = path.join(__dirname, '..', 'dist', 'index.html');

// Simple smoke test to ensure the game page loads in the browser
// This test opens the built application and checks for the main menu.
test('loads Battle Hexes page', async ({ page }) => {
  await page.goto('file://' + indexPath);
  await expect(page.locator('#menu')).toContainText('Battle Hexes');
});
