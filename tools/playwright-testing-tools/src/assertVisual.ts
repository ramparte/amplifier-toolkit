import type { Page } from '@playwright/test';
import { expect } from '@playwright/test';

/**
 * Visual assertion options
 */
export interface VisualOptions {
  /** Pixel difference threshold (0-1, default 0.05 = 5%) */
  threshold?: number;
  
  /** Maximum pixel differences allowed (default 100) */
  maxDiffPixels?: number;
  
  /** Selectors to mask (for dynamic content like timestamps, cursors) */
  mask?: string[];
  
  /** Disable animations before screenshot */
  animations?: 'disabled' | 'allow';
  
  /** Platform-specific baseline (auto-detected if not provided) */
  platform?: 'linux' | 'darwin' | 'win32';
}

/**
 * Visual assertion configuration
 */
export interface VisualAssertion {
  /** Name of the baseline screenshot (without extension) */
  name: string;
  
  /** Options for screenshot comparison */
  options?: VisualOptions;
  
  /** Optional: specific element to screenshot (defaults to full page) */
  element?: string;
}

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
export async function assertVisual(
  page: Page,
  assertion: VisualAssertion
): Promise<void> {
  const {
    name,
    options = {},
    element
  } = assertion;
  
  const {
    threshold = 0.05,
    maxDiffPixels = 100,
    mask = [],
    animations = 'disabled'
  } = options;
  
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
    animations: animations as 'disabled' | 'allow'
  };
  
  // Take screenshot of element or full page
  if (element) {
    const locator = page.locator(element);
    await expect(locator,
      `Visual regression: ${name} (element: ${element})`
    ).toHaveScreenshot(`${name}.png`, screenshotOptions);
  } else {
    await expect(page,
      `Visual regression: ${name} (full page)`
    ).toHaveScreenshot(`${name}.png`, screenshotOptions);
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
export async function updateVisualBaseline(
  page: Page,
  name: string,
  element?: string
): Promise<void> {
  // Set update snapshots flag
  process.env.UPDATE_SNAPSHOTS = 'true';
  
  try {
    await assertVisual(page, { name, element });
  } finally {
    delete process.env.UPDATE_SNAPSHOTS;
  }
}
