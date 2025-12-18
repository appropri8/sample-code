/**
 * Tool output sanitization and validation.
 * Removes dangerous content, limits size, detects injection patterns, and validates structure.
 */

const MAX_TOOL_OUTPUT_LENGTH = 100000; // 100KB
const MAX_LINES = 1000;

export interface ValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Sanitizes tool output before it enters agent context.
 * Removes control characters, limits length, detects injection patterns, normalizes whitespace.
 */
export function sanitizeToolOutput(output: unknown): string {
  // Convert to string if needed
  let text: string;
  if (typeof output === 'string') {
    text = output;
  } else if (typeof output === 'object' && output !== null) {
    text = JSON.stringify(output);
  } else {
    text = String(output);
  }

  // Remove control characters (except newlines, tabs, carriage returns)
  text = text.replace(/[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]/g, '');

  // Limit length
  if (text.length > MAX_TOOL_OUTPUT_LENGTH) {
    text = text.substring(0, MAX_TOOL_OUTPUT_LENGTH) + '\n... [truncated]';
  }

  // Limit lines
  const lines = text.split('\n');
  if (lines.length > MAX_LINES) {
    text = lines.slice(0, MAX_LINES).join('\n') + '\n... [truncated lines]';
  }

  // Remove potential prompt injection patterns (basic heuristic)
  const injectionPatterns = [
    /ignore\s+previous\s+instructions/gi,
    /system:\s*override/gi,
    /\[INST\].*?\[\/INST\]/gi,
    /<\|im_start\|>.*?<\|im_end\|>/gi,
  ];

  for (const pattern of injectionPatterns) {
    if (pattern.test(text)) {
      // Log the detection but don't fail - just remove the pattern
      console.warn('Potential prompt injection pattern detected in tool output');
      text = text.replace(pattern, '[REDACTED]');
    }
  }

  // Normalize whitespace (collapse multiple spaces, but preserve structure)
  text = text.replace(/[ \t]+/g, ' ');
  text = text.replace(/\n{3,}/g, '\n\n');

  return text;
}

/**
 * Validates tool output structure and content.
 * Checks length, null bytes, and JSON nesting depth.
 */
export function validateToolOutput(output: string): ValidationResult {
  const errors: string[] = [];

  // Check length
  if (output.length > MAX_TOOL_OUTPUT_LENGTH) {
    errors.push(`Output exceeds maximum length: ${output.length} > ${MAX_TOOL_OUTPUT_LENGTH}`);
  }

  // Check for null bytes
  if (output.includes('\x00')) {
    errors.push('Output contains null bytes');
  }

  // Check for excessive nesting (if JSON)
  try {
    const parsed = JSON.parse(output);
    const depth = getObjectDepth(parsed);
    if (depth > 20) {
      errors.push(`JSON nesting depth too high: ${depth} > 20`);
    }
  } catch {
    // Not JSON, that's fine
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

function getObjectDepth(obj: unknown, currentDepth = 0): number {
  if (typeof obj !== 'object' || obj === null) {
    return currentDepth;
  }

  if (Array.isArray(obj)) {
    return Math.max(...obj.map(item => getObjectDepth(item, currentDepth + 1)), currentDepth);
  }

  return Math.max(
    ...Object.values(obj).map(value => getObjectDepth(value, currentDepth + 1)),
    currentDepth
  );
}
