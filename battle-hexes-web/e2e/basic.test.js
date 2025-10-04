import { test, expect } from '@playwright/test';
import path from 'path';
import { pathToFileURL } from 'url';

const indexPath = path.join(__dirname, '..', 'dist', 'index.html');
const battlePath = path.join(__dirname, '..', 'dist', 'battle.html');
const indexUrl = pathToFileURL(indexPath).href;
const battleUrl = pathToFileURL(battlePath).href;

test('title screen links to the battle page', async ({ page }) => {
  await page.goto(indexUrl);
  await expect(page.locator('h1')).toHaveText('Battle Hexes');
  await page.locator('a:has-text("Enter Battle")').click();
  await expect(page).toHaveURL(battleUrl);
});

test('battle page still loads game menu', async ({ page }) => {
  await page.goto(battleUrl);
  await expect(page.locator('#menu')).toContainText('Battle Hexes');
});
