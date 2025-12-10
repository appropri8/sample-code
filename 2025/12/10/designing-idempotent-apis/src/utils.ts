import { createHash } from 'crypto';

export function hashString(input: string): string {
  return createHash('sha256').update(input).digest('hex');
}

export function generateIdempotencyKey(
  action: string,
  userId: string,
  context: Record<string, string>
): string {
  const contextStr = Object.entries(context)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}:${v}`)
    .join('-');
  
  const timestamp = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
  
  return `${action}-${userId}-${contextStr}-${timestamp}`;
}

export function validateIdempotencyKey(key: string): boolean {
  // Basic validation: non-empty, reasonable length
  if (!key || key.length === 0 || key.length > 255) {
    return false;
  }
  
  // Should contain some structure (not just random)
  if (key.split('-').length < 2) {
    return false;
  }
  
  return true;
}
