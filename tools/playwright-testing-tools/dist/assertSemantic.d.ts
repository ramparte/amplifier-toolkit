import type { Page } from '@playwright/test';
/**
 * Semantic validation options
 */
export interface SemanticOptions {
    /** Vision model to use */
    model?: 'gpt-4-vision' | 'claude-3-5-sonnet' | 'claude-3-opus';
    /** Number of retries for non-deterministic failures */
    retries?: number;
    /** Temperature for model (0 = deterministic, 1 = creative) */
    temperature?: number;
    /** Maximum tokens for response */
    maxTokens?: number;
    /** Timeout in ms (default 10000) */
    timeout?: number;
}
/**
 * Semantic assertion configuration
 */
export interface SemanticAssertion {
    /** Validation prompt - what to check for */
    prompt: string;
    /** Expected verdict: PASS or FAIL */
    expectedVerdict: 'PASS' | 'FAIL';
    /** Optional: specific element to screenshot (defaults to full page) */
    element?: string;
    /** Options for semantic validation */
    options?: SemanticOptions;
}
/**
 * Semantic validation result
 */
export interface SemanticResult {
    verdict: 'PASS' | 'FAIL';
    reason: string;
    model: string;
    retries: number;
    screenshot?: Buffer;
}
/**
 * Assert semantic correctness using vision model
 *
 * Expensive and slow - use sparingly for critical flows only!
 *
 * @example
 * ```typescript
 * await assertSemantic(page, {
 *   prompt: `Check this Word-like editor:
 *   1. Ribbon visible at top with tabs (Home, Insert, Layout)
 *   2. Ribbon height reasonable (~100px, not 250px)
 *   3. Page canvas visible with document content
 *   4. No obvious layout breaks
 *
 *   Answer PASS or FAIL with brief reason.`,
 *   expectedVerdict: 'PASS',
 *   options: {
 *     model: 'claude-3-5-sonnet',
 *     retries: 2
 *   }
 * });
 * ```
 */
export declare function assertSemantic(page: Page, assertion: SemanticAssertion): Promise<SemanticResult>;
/**
 * Quick semantic check - fast fail for obviously broken UIs
 *
 * Uses a simple prompt and fast model to quickly catch major breaks.
 * Use this as a pre-filter before expensive detailed checks.
 *
 * @example
 * ```typescript
 * // Quick check before detailed validation
 * await assertSemanticQuick(page, {
 *   prompt: 'Does this look like a functional Word-like editor? PASS or FAIL.',
 *   expectedVerdict: 'PASS'
 * });
 * ```
 */
export declare function assertSemanticQuick(page: Page, assertion: Omit<SemanticAssertion, 'options'>): Promise<SemanticResult>;
//# sourceMappingURL=assertSemantic.d.ts.map