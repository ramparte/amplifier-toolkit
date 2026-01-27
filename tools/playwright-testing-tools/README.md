# Playwright Testing Tools

Three-tier testing toolkit for Playwright that balances speed, repeatability, and robustness.

## The Three-Tier Pyramid

```
┌─────────────────────────────────────────────────┐
│  Tier 3: Semantic (Vision Model)               │  ← Expensive, slow, catches subtle issues
│  - Uses Claude/GPT-4 Vision API                 │     Use sparingly for critical flows
│  - Understands "looks right to humans"          │
│  - Cost: ~$0.01-0.05 per check                 │
│  - Speed: 2-5 seconds                           │
├─────────────────────────────────────────────────┤
│  Tier 2: Visual (Pixel Matching)                │  ← Moderate cost, catches layout breaks
│  - Playwright screenshot comparison             │     Use for key UI states
│  - Detects visual regressions                   │
│  - Cost: Free (CI storage)                      │
│  - Speed: 100-500ms                             │
├─────────────────────────────────────────────────┤
│  Tier 1: Structural (DOM Assertions)            │  ← Fast, repeatable, catches most bugs
│  - CSS properties, counts, visibility           │     Use everywhere
│  - Deterministic and stable                     │
│  - Cost: Free                                   │
│  - Speed: 50-200ms                              │
└─────────────────────────────────────────────────┘
```

## Installation

```bash
npm install --save-dev @amplifier-toolkit/playwright-testing-tools @playwright/test
```

## Quick Start

```typescript
import { test } from '@playwright/test';
import { assertStructure, assertVisual, assertSemantic } from '@amplifier-toolkit/playwright-testing-tools';

test('My app looks correct', async ({ page }) => {
  await page.goto('http://localhost:3000');
  
  // Tier 1: Fast structural check (50ms)
  await assertStructure(page, {
    '.header': { exists: true, css: { height: { max: 100 } } },
    '.main-content': { exists: true, visible: true }
  });
  
  // Tier 2: Visual regression (300ms)
  await assertVisual(page, {
    name: 'home-page',
    options: { threshold: 0.05 }
  });
  
  // Tier 3: Semantic check (3s, optional)
  if (process.env.ANTHROPIC_API_KEY) {
    await assertSemantic(page, {
      prompt: 'Does this page look professional? PASS or FAIL.',
      expectedVerdict: 'PASS'
    });
  }
});
```

## API Reference

### Tier 1: `assertStructure(page, assertions)`

Fast DOM assertions - use everywhere.

```typescript
await assertStructure(page, {
  '.selector': {
    exists?: boolean;
    count?: { min?: number; max?: number; exact?: number };
    css?: Record<string, string | { min?: number; max?: number }>;
    text?: string | RegExp;
    attributes?: Record<string, string>;
    visible?: boolean;
  }
});
```

**Example:**
```typescript
await assertStructure(page, {
  '.ribbon': {
    exists: true,
    css: {
      display: 'flex',
      height: { max: 130 }
    }
  },
  '.ribbon-button': {
    count: { min: 10 }
  }
});
```

### Tier 2: `assertVisual(page, config)`

Pixel-perfect screenshot comparison.

```typescript
await assertVisual(page, {
  name: string;              // Baseline name
  element?: string;          // Optional: screenshot specific element
  options?: {
    threshold?: number;      // 0-1, default 0.05 (5% difference OK)
    maxDiffPixels?: number;  // default 100
    mask?: string[];         // Selectors to mask (dynamic content)
    animations?: 'disabled' | 'allow';
  }
});
```

**Example:**
```typescript
await assertVisual(page, {
  name: 'ribbon-layout',
  element: '.ribbon',
  options: {
    threshold: 0.05,
    maxDiffPixels: 100,
    mask: ['.cursor', '.timestamp']
  }
});
```

### Tier 3: `assertSemantic(page, config)`

Vision model validation - expensive, use sparingly.

```typescript
await assertSemantic(page, {
  prompt: string;
  expectedVerdict: 'PASS' | 'FAIL';
  element?: string;
  options?: {
    model?: 'claude-3-5-sonnet' | 'gpt-4-vision' | 'claude-3-opus';
    retries?: number;        // default 1
    temperature?: number;    // default 0
    maxTokens?: number;      // default 500
    timeout?: number;        // default 10000ms
  }
});
```

**Example:**
```typescript
await assertSemantic(page, {
  prompt: `Check this Word-like editor:
  1. Ribbon visible at top (~100px height, not 250px)
  2. Three tabs: Home, Insert, Layout
  3. Looks professional and functional
  
  Answer PASS or FAIL with brief reason.`,
  expectedVerdict: 'PASS',
  options: {
    model: 'claude-3-5-sonnet',
    retries: 1
  }
});
```

## When to Use Each Tier

| Scenario | Tier 1 | Tier 2 | Tier 3 |
|----------|--------|--------|--------|
| Development feedback | ✅ Always | ❌ No | ❌ No |
| CI pipeline | ✅ Always | ✅ Yes | ❌ No |
| Pre-release validation | ✅ Always | ✅ Yes | ✅ Critical flows only |
| Bug investigation | ✅ Always | ✅ If needed | ✅ One-off checks |

## Cost-Benefit Analysis

| Tier | Speed | Cost | Bugs Caught | False Positives |
|------|-------|------|-------------|-----------------|
| Structural | 50ms | Free | 70% | <1% |
| Visual | 300ms | Free | 25% | 5-10% |
| Semantic | 3s | $0.03 | 5% | 2-5% |

## Environment Variables

For Tier 3 (semantic validation):

```bash
# Claude (recommended)
export ANTHROPIC_API_KEY=your-key-here

# OpenAI (alternative)
export OPENAI_API_KEY=your-key-here
```

## License

MIT
