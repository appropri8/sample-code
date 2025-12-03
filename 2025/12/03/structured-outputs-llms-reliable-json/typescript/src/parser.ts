/**
 * Extract JSON from raw LLM responses.
 */

export function extractJson(text: string): Record<string, any> | any[] {
  // Step 1: Trim whitespace
  text = text.trim();
  
  // Step 2: Remove markdown code blocks
  // Matches ```json ... ``` or ``` ... ```
  text = text.replace(/```(?:json)?\s*\n?(.*?)\n?```/gs, '$1');
  text = text.trim();
  
  // Step 3: Find JSON object/array
  // Look for first { or [
  let start = text.indexOf('{');
  if (start === -1) {
    start = text.indexOf('[');
  }
  if (start === -1) {
    throw new Error('No JSON found in response');
  }
  
  // Step 4: Find matching closing brace/bracket
  let depth = 0;
  let inString = false;
  let escapeNext = false;
  
  for (let i = start; i < text.length; i++) {
    const char = text[i];
    
    if (escapeNext) {
      escapeNext = false;
      continue;
    }
    
    if (char === '\\') {
      escapeNext = true;
      continue;
    }
    
    if (char === '"' && !escapeNext) {
      inString = !inString;
      continue;
    }
    
    if (inString) {
      continue;
    }
    
    if (char === '{' || char === '[') {
      depth++;
    } else if (char === '}' || char === ']') {
      depth--;
      if (depth === 0) {
        const jsonStr = text.substring(start, i + 1);
        try {
          return JSON.parse(jsonStr);
        } catch (e: any) {
          throw new Error(`Invalid JSON: ${e.message}`);
        }
      }
    }
  }
  
  throw new Error('Unclosed JSON structure');
}

export function extractJsonSimple(text: string): Record<string, any> | any[] | null {
  text = text.trim();
  
  // Try parsing the whole text first
  try {
    return JSON.parse(text);
  } catch {
    // Fall back to full extraction
    try {
      return extractJson(text);
    } catch {
      return null;
    }
  }
}

