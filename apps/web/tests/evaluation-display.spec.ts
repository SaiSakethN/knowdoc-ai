import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';

test('real local benchmark results render with provisional warnings', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop', 'Desktop evidence screenshot only');
  const credentialsPath = '../../data/demo-credentials.json';
  test.skip(!existsSync(credentialsPath), 'Requires the locally generated demo account and actual benchmark run');
  const credentials = JSON.parse(readFileSync(credentialsPath, 'utf8'));
  await page.goto('/');
  await page.getByLabel('Email address').fill(credentials.email);
  await page.getByLabel('Password', { exact: true }).fill(credentials.password);
  await page.getByRole('button', { name: 'Sign in', exact: true }).click();
  await page.getByRole('button', { name: 'Evaluations', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'knowdoc-80-v1' }).first()).toBeVisible();
  await expect(page.getByRole('cell', { name: 'hybrid_rerank', exact: true })).toBeVisible();
  await expect(page.getByText('Provisional benchmark', { exact: true }).first()).toBeVisible();
  await expect(page.getByText('Deterministic expected-status checks', { exact: false }).first()).toBeVisible();
  await page.screenshot({ path: '../../artifacts/screenshots/desktop-evaluation.png', fullPage: true });
});
