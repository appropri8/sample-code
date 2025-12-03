/**
 * Auto-repair common JSON issues.
 */

export function repairJson(text: string): Record<string, any> | any[] | null {
  if (!text || !text.trim()) {
    return null;
  }
  
  // Remove comments (simple cases)
  // Remove // comments
  text = text.replace(/\/\/.*$/gm, '');
  // Remove /* */ comments
  text = text.replace(/\/\*.*?\*\//gs, '');
  
  // Remove trailing commas before } or ]
  text = text.replace(/,(\s*[}\]])/g, '$1');
  
  // Try to fix single quotes to double quotes (very simple cases only)
  // Match: 'key': 'value' or 'key': "value"
  text = text.replace(/'([^']*)':\s*/g, '"$1": ');
  // Match: "key": 'value'
  text = text.replace(/:\s*'([^']*)'/g, ': "$1"');
  
  // Trim whitespace
  text = text.trim();
  
  // Try parsing
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export function fixTrailingComma(text: string): string {
  return text.replace(/,(\s*[}\]])/g, '$1');
}

export function removeComments(text: string): string {
  // Remove // comments
  text = text.replace(/\/\/.*$/gm, '');
  // Remove /* */ comments
  text = text.replace(/\/\*.*?\*\//gs, '');
  return text;
}

