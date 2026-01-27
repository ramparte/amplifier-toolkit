/**
 * Call vision model for semantic validation
 */
async function callVisionModel(screenshot, prompt, options) {
    const { model, temperature, maxTokens, timeout } = options;
    // Check for API keys
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    const openaiKey = process.env.OPENAI_API_KEY;
    if (model.startsWith('claude-') && !anthropicKey) {
        throw new Error('ANTHROPIC_API_KEY not set for Claude model');
    }
    if (model === 'gpt-4-vision' && !openaiKey) {
        throw new Error('OPENAI_API_KEY not set for GPT-4 Vision model');
    }
    // Encode screenshot as base64
    const base64Image = screenshot.toString('base64');
    try {
        if (model.startsWith('claude-')) {
            return await callClaude(base64Image, prompt, model, temperature, maxTokens, timeout);
        }
        else if (model === 'gpt-4-vision') {
            return await callGPT4Vision(base64Image, prompt, temperature, maxTokens, timeout);
        }
        else {
            throw new Error(`Unsupported model: ${model}`);
        }
    }
    catch (error) {
        throw new Error(`Vision model call failed: ${error instanceof Error ? error.message : String(error)}`);
    }
}
/**
 * Call Claude API for vision analysis
 */
async function callClaude(base64Image, prompt, model, temperature, maxTokens, timeout) {
    const apiKey = process.env.ANTHROPIC_API_KEY;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': apiKey,
                'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
                model: model,
                max_tokens: maxTokens,
                temperature: temperature,
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'image',
                                source: {
                                    type: 'base64',
                                    media_type: 'image/png',
                                    data: base64Image
                                }
                            },
                            {
                                type: 'text',
                                text: `${prompt}\n\nRespond in this exact format:\nVERDICT: [PASS or FAIL]\nREASON: [brief explanation]`
                            }
                        ]
                    }
                ]
            }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`Claude API error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        const text = data.content[0].text;
        return parseVerdictResponse(text);
    }
    catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}
/**
 * Call GPT-4 Vision API for vision analysis
 */
async function callGPT4Vision(base64Image, prompt, temperature, maxTokens, timeout) {
    const apiKey = process.env.OPENAI_API_KEY;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);
    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${apiKey}`
            },
            body: JSON.stringify({
                model: 'gpt-4-vision-preview',
                max_tokens: maxTokens,
                temperature: temperature,
                messages: [
                    {
                        role: 'user',
                        content: [
                            {
                                type: 'image_url',
                                image_url: {
                                    url: `data:image/png;base64,${base64Image}`
                                }
                            },
                            {
                                type: 'text',
                                text: `${prompt}\n\nRespond in this exact format:\nVERDICT: [PASS or FAIL]\nREASON: [brief explanation]`
                            }
                        ]
                    }
                ]
            }),
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (!response.ok) {
            throw new Error(`OpenAI API error: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        const text = data.choices[0].message.content;
        return parseVerdictResponse(text);
    }
    catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}
/**
 * Parse verdict response from model
 */
function parseVerdictResponse(text) {
    // Extract verdict
    const verdictMatch = text.match(/VERDICT:\s*(PASS|FAIL)/i);
    if (!verdictMatch) {
        throw new Error(`Could not parse verdict from response: ${text}`);
    }
    const verdict = verdictMatch[1].toUpperCase();
    // Extract reason
    const reasonMatch = text.match(/REASON:\s*(.+?)(?:\n|$)/i);
    const reason = reasonMatch ? reasonMatch[1].trim() : 'No reason provided';
    return { verdict, reason };
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
export async function assertSemantic(page, assertion) {
    const { prompt, expectedVerdict, element, options = {} } = assertion;
    const { model = 'claude-3-5-sonnet', retries = 1, temperature = 0, maxTokens = 500, timeout = 10000 } = options;
    const fullOptions = { model, retries, temperature, maxTokens, timeout };
    // Take screenshot
    let screenshot;
    if (element) {
        const locator = page.locator(element);
        screenshot = await locator.screenshot();
    }
    else {
        screenshot = await page.screenshot({ fullPage: true });
    }
    // Try validation with retries
    let lastError = null;
    let attemptCount = 0;
    for (let attempt = 0; attempt <= retries; attempt++) {
        attemptCount++;
        try {
            const result = await callVisionModel(screenshot, prompt, fullOptions);
            // Check if verdict matches expectation
            if (result.verdict === expectedVerdict) {
                return {
                    ...result,
                    model,
                    retries: attemptCount - 1,
                    screenshot
                };
            }
            else {
                // Verdict mismatch
                const error = new Error(`Semantic validation failed\n` +
                    `Expected: ${expectedVerdict}\n` +
                    `Got: ${result.verdict}\n` +
                    `Reason: ${result.reason}\n` +
                    `Model: ${model}\n` +
                    `Attempts: ${attemptCount}/${retries + 1}`);
                if (attempt === retries) {
                    throw error;
                }
                lastError = error;
                // Retry after brief delay
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        catch (error) {
            lastError = error instanceof Error ? error : new Error(String(error));
            if (attempt === retries) {
                throw lastError;
            }
            // Retry after brief delay
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    }
    throw lastError || new Error('Semantic validation failed with unknown error');
}
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
export async function assertSemanticQuick(page, assertion) {
    return assertSemantic(page, {
        ...assertion,
        options: {
            model: 'claude-3-5-sonnet', // Fast and good enough
            retries: 0,
            temperature: 0,
            maxTokens: 200,
            timeout: 5000
        }
    });
}
//# sourceMappingURL=assertSemantic.js.map