import { z } from 'zod';
import { ZodSchema } from 'zod';

/**
 * Validate JSON data against a Zod schema.
 */
export function validateJson<T>(
  jsonData: unknown,
  schema: ZodSchema<T>
): T {
  const result = schema.safeParse(jsonData);
  
  if (!result.success) {
    const errors = result.error.errors.map(err => ({
      field: err.path.join('.'),
      message: err.message,
      code: err.code,
    }));
    
    throw new Error(`Validation failed: ${JSON.stringify(errors, null, 2)}`);
  }
  
  return result.data;
}

/**
 * Format a Zod error into a readable string.
 */
export function formatValidationError(error: z.ZodError): string {
  return error.errors
    .map(err => `${err.path.join('.')}: ${err.message}`)
    .join('; ');
}

