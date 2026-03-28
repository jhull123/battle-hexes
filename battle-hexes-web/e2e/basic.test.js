import { test, expect } from '@playwright/test';

test('title screen loads and can start a mock game', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('heading', { level: 1, name: 'Battle Hexes' })).toBeVisible();

  await expect(page.locator('#scenario-select')).toHaveValue('mock_scenario');
  await expect(page.locator('#player1-type')).toHaveValue('human');
  await expect(page.locator('#player2-type')).toHaveValue('random');

  await page.getByRole('button', { name: 'Enter Battle' }).click();

  await expect(page).toHaveURL(/\/battle\.html\?gameId=mock-game$/);
  await expect(page.locator('#menu')).toBeVisible();
  await expect(page.getByRole('heading', { level: 2, name: 'Battle Hexes' })).toBeVisible();
});
