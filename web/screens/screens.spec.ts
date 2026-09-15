/**
 * Every page, at every device in playwright.config.ts, in both themes.
 *
 * `pnpm screens` writes them to screenshots/<device>/<page>-<theme>.png. It is
 * a look, not an assertion: the only thing that fails a run is a page that
 * never rendered its heading.
 *
 * What this can't show you is what a real phone does with env(safe-area-inset-*)
 * or with dvh as the URL bar collapses. Neither is emulated. For those, run the
 * dev server and open it on the device.
 */

import { expect, test } from '@playwright/test'
import { NOW, SCREENS, stubApi } from './fixtures.ts'

const THEMES = ['light', 'dark'] as const

for (const screen of SCREENS) {
  for (const theme of THEMES) {
    test(`${screen.name} ${theme}`, async ({ page }, info) => {
      await page.clock.setFixedTime(NOW)
      await page.emulateMedia({ colorScheme: theme })
      await stubApi(page, screen.me)

      // The shell fetches accounts and history on boot, and the dashboard is
      // half empty until both land.
      const loaded = screen.me?.onboarded
        ? Promise.all([
            page.waitForResponse('**/api/accounts/selection'),
            page.waitForResponse('**/api/transactions*'),
          ])
        : null

      await page.goto(screen.path)
      await loaded

      await expect(
        page.getByRole('heading', { level: 1, name: screen.heading }),
      ).toBeVisible()

      // Otherwise the capture can catch the fallback stack mid-swap.
      await page.evaluate(async () => {
        await document.fonts.ready
      })

      await page.screenshot({
        path: `screenshots/${info.project.name}/${screen.name}-${theme}.png`,
        fullPage: true,
      })
    })
  }
}
