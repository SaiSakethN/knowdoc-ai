import { defineConfig, devices } from '@playwright/test';
const runId = process.env.KNOWDOC_TEST_RUN || new Date().toISOString().replaceAll(/[:.]/g, '-');
export default defineConfig({
  testDir: './tests', timeout: 90000, expect: { timeout: 30000 }, workers: 1,
  outputDir: `../../artifacts/browser/${runId}`,
  reporter: [['list'], ['json', { outputFile: `../../artifacts/browser/${runId}/results.json` }]],
  use: { baseURL: process.env.KNOWDOC_TEST_URL || 'http://127.0.0.1:8000', trace: 'retain-on-failure', screenshot: 'only-on-failure' },
  projects: [{ name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['iPhone 13'], defaultBrowserType: 'chromium' } }],
});
