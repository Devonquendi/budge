import { defineConfig, devices } from '@playwright/test'

/**
 * The device list the screenshot harness runs over. The iPhone and iPad presets
 * are WebKit and the rest Chromium, which is the point: Safari is the engine
 * most of this app's phone traffic will be, and it is the one a resized desktop
 * Chrome window can never stand in for.
 *
 * `pnpm exec playwright install` once, to fetch those browsers.
 */
export default defineConfig({
  testDir: 'screens',
  outputDir: 'screenshots/.runs',
  fullyParallel: true,
  reporter: 'list',

  use: {
    baseURL: 'http://localhost:5173',
    // Fixed, so dates and money format the same way on any machine.
    locale: 'en-NZ',
    timezoneId: 'Pacific/Auckland',
  },

  projects: [
    { name: 'iphone', use: devices['iPhone 15'] },
    { name: 'iphone-landscape', use: devices['iPhone 15 landscape'] },
    { name: 'pixel', use: devices['Pixel 7'] },
    { name: 'ipad', use: devices['iPad Mini'] },
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 900 } },
    },
  ],

  // No backend: screens/fixtures.ts answers /api inside the browser.
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    timeout: 60_000,
  },
})
