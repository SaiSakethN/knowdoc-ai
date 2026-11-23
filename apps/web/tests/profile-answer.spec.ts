import { test, expect } from '@playwright/test';

test('simple profile questions default to concise answers with one clickable reference', async ({ page }, testInfo) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Create an account', exact: true }).click();
  await page.getByLabel('Email address').fill(`profile-${testInfo.project.name}-${Date.now()}@example.com`);
  await page.getByLabel('Password', { exact: true }).fill('profile-test-password');
  await page.getByRole('button', { name: 'Create private workspace' }).click();
  await expect(page.getByRole('combobox', { name: 'Answer mode' })).toHaveValue('generate');
  await page.getByRole('button', { name: 'Create your first collection' }).click();
  await page.getByLabel('Collection name').fill('Profile answers');
  await page.getByRole('dialog').getByRole('button', { name: 'Create collection', exact: true }).click();
  await page.getByRole('button', { name: 'Add your first document' }).click();
  await page.locator('input[type=file]').setInputFiles({ name: 'profile.md', mimeType: 'text/markdown', buffer: Buffer.from('# Self Introduction\nMy name is Morgan Rivera. I am a Data Engineer with five years of experience.\nCurrently, I am working at Example Labs, where I build pipelines. Previously, I worked as an Analyst.') });
  await expect(page.getByRole('status')).toContainText('accepted');
  await page.getByRole('button', { name: 'Close upload' }).click();
  await expect(page.getByRole('button', { name: /Find the right guidance/ })).toBeVisible();
  for (const [question, expected] of [['what is your name', 'Morgan Rivera.'], ['what is your current role', 'Data Engineer at Example Labs.']]) {
    await page.getByRole('textbox', { name: 'Ask a question' }).fill(question);
    await page.getByRole('button', { name: 'Send question' }).click();
    const message = page.locator('.message').last();
    await expect(message.locator('.answer-text')).toContainText(expected);
    await expect(message.getByText('Document fact | source verified', { exact: true })).toBeVisible();
    await expect(message.getByRole('button', { name: 'Open reference 1' })).toBeVisible();
    await expect(message.locator('.evidence-card')).not.toBeVisible();
    await message.getByRole('button', { name: 'Open reference 1' }).click();
    await expect(page.getByLabel('Source evidence')).toContainText('Morgan Rivera');
    await page.getByRole('button', { name: 'Close source' }).click();
  }
  await page.screenshot({ path: `../../artifacts/screenshots/${testInfo.project.name}-concise-profile.png`, fullPage: true });
});
