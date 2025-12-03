import { z } from 'zod';
import { ZodSchema } from 'zod';
import { StructuredLLM } from './llm-client';
import { extractJson } from './parser';
import { validateJson } from './validator';
import { repairJson } from './repair';
import { buildStructuredPrompt, addErrorFeedback } from './prompt-builder';

/**
 * Get structured output from LLM with parsing, validation, and retry logic.
 */
export async function getStructuredOutput<T>(
  llm: StructuredLLM,
  prompt: string,
  schema: ZodSchema<T>,
  maxRetries: number = 3,
  enableRepair: boolean = true,
  useJsonMode: boolean = false
): Promise<T> {
  const schemaName = schema.constructor.name;
  const modelName = llm.modelName;
  const originalPrompt = prompt;
  let lastError: string | null = null;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const startTime = Date.now();

    try {
      // Call LLM
      const rawResponse = await llm.generate(prompt, useJsonMode);

      // Try repair first (if enabled)
      let jsonData: any = null;
      if (enableRepair) {
        jsonData = repairJson(rawResponse);
      }

      // Extract JSON if repair didn't work
      if (jsonData === null) {
        try {
          jsonData = extractJson(rawResponse);
        } catch (e: any) {
          lastError = `JSON parsing failed: ${e.message}`;
          const durationMs = Date.now() - startTime;

          // Log error (in production, use proper logging)
          console.warn(`Parse error (attempt ${attempt + 1}): ${lastError}`);

          if (attempt < maxRetries - 1) {
            prompt = addErrorFeedback(originalPrompt, lastError, rawResponse);
            continue;
          }
          throw new Error(`Failed to parse JSON after ${maxRetries} attempts: ${lastError}`);
        }
      }

      // Validate
      try {
        const result = validateJson(jsonData, schema);
        const durationMs = Date.now() - startTime;

        // Log success (in production, use proper logging)
        console.log(`Success (attempt ${attempt + 1}, ${durationMs}ms)`);

        return result;
      } catch (e: any) {
        lastError = `Schema validation failed: ${e.message}`;
        const durationMs = Date.now() - startTime;

        // Log error (in production, use proper logging)
        console.warn(`Validation error (attempt ${attempt + 1}): ${lastError}`);

        if (attempt < maxRetries - 1) {
          prompt = addErrorFeedback(originalPrompt, lastError, rawResponse);
          continue;
        }
        throw new Error(`Failed to validate JSON after ${maxRetries} attempts: ${lastError}`);
      }
    } catch (e: any) {
      // Re-throw if it's our error
      if (e.message.includes('Failed to')) {
        throw e;
      }
      // Otherwise, it's an LLM call error
      lastError = `LLM call failed: ${e.message}`;
      const durationMs = Date.now() - startTime;

      // Log error (in production, use proper logging)
      console.warn(`LLM error (attempt ${attempt + 1}): ${lastError}`);

      if (attempt < maxRetries - 1) {
        // Don't retry on timeout/API errors immediately
        await new Promise(resolve => setTimeout(resolve, 1000));
        continue;
      }
      throw new Error(`LLM call failed after ${maxRetries} attempts: ${lastError}`);
    }
  }

  throw new Error(`Failed after ${maxRetries} attempts. Last error: ${lastError}`);
}

