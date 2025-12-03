import { z } from 'zod';
import { ZodSchema } from 'zod';

/**
 * Build a prompt that asks for structured JSON output.
 */
export function buildStructuredPrompt(
  schema: ZodSchema,
  inputText: string,
  examples?: Record<string, any>[],
  taskDescription?: string
): string {
  // Convert Zod schema to JSON Schema
  const schemaJson = zodToJsonSchema(schema);
  
  // Build examples text
  let examplesText = '';
  if (examples && examples.length > 0) {
    examplesText = '\n\nExamples:\n';
    for (const ex of examples) {
      examplesText += JSON.stringify(ex, null, 2) + '\n';
    }
  }
  
  // Default task description
  if (!taskDescription) {
    taskDescription = 'Extract information from the text and return it as JSON.';
  }
  
  const prompt = `You are a JSON API. ${taskDescription}

Text to process:
${inputText}

Required JSON schema:
${JSON.stringify(schemaJson, null, 2)}
${examplesText}
Rules:
1. Return ONLY the JSON object, no other text
2. Do not include markdown code blocks (\`\`\`json or \`\`\`)
3. Do not include explanations or comments
4. Use double quotes for all strings
5. No trailing commas
6. Escape special characters in strings (\\n, \\", \\\\)
7. All required fields must be present
8. Do not add fields that are not in the schema

Return the JSON now:`;
  
  return prompt;
}

/**
 * Add error feedback to a prompt for retry.
 */
export function addErrorFeedback(
  originalPrompt: string,
  errorMessage: string,
  rawResponse?: string
): string {
  let feedback = `\n\nPrevious attempt failed with error: ${errorMessage}`;
  
  if (rawResponse) {
    const truncated = rawResponse.length > 200 
      ? rawResponse.substring(0, 200) + '...' 
      : rawResponse;
    feedback += `\nResponse received: ${truncated}`;
  }
  
  feedback += '\n\nPlease fix the issue and return valid JSON matching the schema.';
  
  return originalPrompt + feedback;
}

/**
 * Simple Zod to JSON Schema converter (basic implementation).
 * For production, use a library like zod-to-json-schema.
 */
function zodToJsonSchema(schema: ZodSchema): Record<string, any> {
  // This is a simplified version. In production, use zod-to-json-schema library.
  const jsonSchema: Record<string, any> = {
    type: 'object',
    properties: {},
    required: [],
  };
  
  // This is a placeholder - actual implementation would need to traverse the Zod schema
  // For now, return a basic structure
  return jsonSchema;
}

