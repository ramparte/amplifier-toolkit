import { expect } from '@playwright/test';
/**
 * Assert visual appearance matches baseline
 *
 * Uses Playwright's screenshot comparison with sensible defaults for robustness.
 *
 * @example
 * ```typescript
 * // Full page
 * await assertVisual(page, {
 *   name: 'homepage',
 *   options: { threshold: 0.05 }
 * });
 *
 * // Specific element
 * await assertVisual(page, {
 *   name: 'ribbon',
 *   element: '.ribbon',
 *   options: { mask: ['.timestamp'] }
 * });
 * ```
 */
export async function assertVisual(page, assertion) {
    const { name, options = {}, element } = assertion;
    const { threshold = 0.05, maxDiffPixels = 100, mask = [], animations = 'disabled' } = options;
    // Disable animations for consistent screenshots
    if (animations === 'disabled') {
        await page.addStyleTag({
            content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
        }
      `
        });
    }
    // Wait for any pending renders
    await page.waitForLoadState('networkidle');
    // Build mask locators
    const maskLocators = mask.map(selector => page.locator(selector));
    // Screenshot options
    const screenshotOptions = {
        threshold,
        maxDiffPixels,
        mask: maskLocators,
        animations: animations
    };
    // Take screenshot of element or full page
    if (element) {
        const locator = page.locator(element);
        await expect(locator, `Visual regression: ${name} (element: ${element})`).toHaveScreenshot(`${name}.png`, screenshotOptions);
    }
    else {
        await expect(page, `Visual regression: ${name} (full page)`).toHaveScreenshot(`${name}.png`, screenshotOptions);
    }
}
/**
 * Update visual baseline for a specific test
 *
 * This is a convenience function for updating baselines.
 * In practice, you'd run: npm run test:visual:update
 *
 * @example
 * ```typescript
 * // In CI or when intentionally updating
 * if (process.env.UPDATE_SNAPSHOTS) {
 *   await updateVisualBaseline(page, 'ribbon');
 * }
 * ```
 */
export async function updateVisualBaseline(page, name, element) {
    // Set update snapshots flag
    process.env.UPDATE_SNAPSHOTS = 'true';
    try {
        await assertVisual(page, { name, element });
    }
    finally {
        delete process.env.UPDATE_SNAPSHOTS;
    }
}
//# sourceMappingURL=assertVisual.js.map