import { expect } from '@playwright/test';
/**
 * Parse CSS value to numeric pixels
 */
function parseCSSDimension(value, basePixels = 16) {
    const match = value.match(/^([\d.]+)(px|in|pt|em|rem|vh|vw)?$/);
    if (!match)
        return 0;
    const num = parseFloat(match[1]);
    const unit = match[2] || 'px';
    switch (unit) {
        case 'px': return num;
        case 'in': return num * 96;
        case 'pt': return num * 96 / 72;
        case 'em':
        case 'rem': return num * basePixels;
        case 'vh': return num * window.innerHeight / 100;
        case 'vw': return num * window.innerWidth / 100;
        default: return num;
    }
}
/**
 * Assert CSS property matches expectation
 */
async function assertCSS(element, property, assertion, selector) {
    const value = await element.evaluate((el, prop) => {
        return window.getComputedStyle(el).getPropertyValue(prop);
    }, property);
    if (typeof assertion === 'string') {
        expect(value, `${selector}: ${property} should be "${assertion}"`).toBe(assertion);
        return;
    }
    const numericValue = parseCSSDimension(value);
    if (assertion.min !== undefined) {
        expect(numericValue, `${selector}: ${property} (${value}) should be >= ${assertion.min}px`).toBeGreaterThanOrEqual(assertion.min);
    }
    if (assertion.max !== undefined) {
        expect(numericValue, `${selector}: ${property} (${value}) should be <= ${assertion.max}px`).toBeLessThanOrEqual(assertion.max);
    }
    if (assertion.approx !== undefined && assertion.tolerance !== undefined) {
        const target = parseCSSDimension(assertion.approx);
        const tolerance = parseCSSDimension(assertion.tolerance);
        expect(Math.abs(numericValue - target), `${selector}: ${property} (${value}) should be ~${assertion.approx} ± ${assertion.tolerance}`).toBeLessThanOrEqual(tolerance);
    }
}
/**
 * Assert element count matches expectation
 */
async function assertCount(elements, assertion, selector) {
    const count = await elements.count();
    if (assertion.exact !== undefined) {
        expect(count, `${selector}: should have exactly ${assertion.exact} elements`).toBe(assertion.exact);
    }
    if (assertion.min !== undefined) {
        expect(count, `${selector}: should have at least ${assertion.min} elements`).toBeGreaterThanOrEqual(assertion.min);
    }
    if (assertion.max !== undefined) {
        expect(count, `${selector}: should have at most ${assertion.max} elements`).toBeLessThanOrEqual(assertion.max);
    }
}
/**
 * Main assertion function - validates DOM structure
 */
export async function assertStructure(page, assertions) {
    for (const [selector, assertion] of Object.entries(assertions)) {
        const elements = page.locator(selector);
        if (assertion.exists !== undefined) {
            if (assertion.exists) {
                await expect(elements.first(), `${selector}: should exist`).toBeAttached();
            }
            else {
                await expect(elements, `${selector}: should not exist`).toHaveCount(0);
            }
        }
        if (assertion.count) {
            await assertCount(elements, assertion.count, selector);
        }
        const element = elements.first();
        if (assertion.visible !== undefined) {
            if (assertion.visible) {
                await expect(element, `${selector}: should be visible`).toBeVisible();
            }
            else {
                await expect(element, `${selector}: should not be visible`).not.toBeVisible();
            }
        }
        if (assertion.css) {
            for (const [property, cssAssertion] of Object.entries(assertion.css)) {
                await assertCSS(element, property, cssAssertion, selector);
            }
        }
        if (assertion.text !== undefined) {
            if (typeof assertion.text === 'string') {
                await expect(element, `${selector}: should contain text "${assertion.text}"`).toContainText(assertion.text);
            }
            else {
                await expect(element, `${selector}: should match pattern ${assertion.text}`).toHaveText(assertion.text);
            }
        }
        if (assertion.attributes) {
            for (const [attr, value] of Object.entries(assertion.attributes)) {
                await expect(element, `${selector}: attribute ${attr} should be "${value}"`).toHaveAttribute(attr, value);
            }
        }
    }
}
//# sourceMappingURL=assertStructure.js.map