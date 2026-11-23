import { test, expect } from '@playwright/test';

test('sign out unmounts all private workspace state before another account signs in', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Create an account', exact: true }).click();
  await page.getByLabel('Email address').fill(`isolation-owner-${Date.now()}@example.com`);
  await page.getByLabel('Password', { exact: true }).fill('isolation-test-password');
  await page.getByRole('button', { name: 'Create private workspace' }).click();
  await page.getByRole('button', { name: 'Create your first collection' }).click();
  const privateName = `Private collection sentinel ${Date.now()}`;
  await page.getByLabel('Collection name').fill(privateName);
  await page.getByRole('dialog').getByRole('button', { name: 'Create collection', exact: true }).click();
  await expect(page.getByRole('combobox', { name: 'Collection scope' })).toHaveValue(/.+/);
  await page.getByTitle('Sign out').click();
  await page.getByRole('button', { name: 'Create an account', exact: true }).click();
  await page.getByLabel('Email address').fill(`isolation-other-${Date.now()}@example.com`);
  await page.getByLabel('Password', { exact: true }).fill('isolation-test-password');
  await page.getByRole('button', { name: 'Create private workspace' }).click();
  await expect(page.getByRole('button', { name: 'Create your first collection' })).toBeVisible();
  await expect(page.getByRole('option', { name: privateName })).toHaveCount(0);
  await expect(page.getByText(privateName, { exact: true })).toHaveCount(0);
});
