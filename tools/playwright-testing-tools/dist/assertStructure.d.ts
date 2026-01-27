import type { Page } from '@playwright/test';
/**
 * CSS property assertion - can be exact value or range
 */
export type CSSAssertion = string | {
    min?: number;
    max?: number;
    approx?: string;
    tolerance?: string;
};
/**
 * Element count assertion
 */
export interface CountAssertion {
    min?: number;
    max?: number;
    exact?: number;
}
/**
 * Structural assertion for a single selector
 */
export interface ElementAssertion {
    exists?: boolean;
    count?: CountAssertion;
    css?: Record<string, CSSAssertion>;
    text?: string | RegExp;
    attributes?: Record<string, string>;
    visible?: boolean;
}
/**
 * Map of selectors to their assertions
 */
export interface StructuralAssertion {
    [selector: string]: ElementAssertion;
}
/**
 * Main assertion function - validates DOM structure
 */
export declare function assertStructure(page: Page, assertions: StructuralAssertion): Promise<void>;
//# sourceMappingURL=assertStructure.d.ts.map