import type { Page } from '@playwright/test';
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
export declare function assertVisual(page: Page, assertion: VisualAssertion): Promise<void>;
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
export declare function updateVisualBaseline(page: Page, name: string, element?: string): Promise<void>;
//# sourceMappingURL=assertVisual.d.ts.map