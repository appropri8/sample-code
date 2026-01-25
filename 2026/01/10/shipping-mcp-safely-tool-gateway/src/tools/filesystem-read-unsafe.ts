import * as fs from 'fs';
import * as path from 'path';

/**
 * UNSAFE VERSION - DO NOT USE IN PRODUCTION
 * 
 * This demonstrates what NOT to do:
 * - No path validation
 * - No size limits
 * - No sandboxing
 * - Direct filesystem access
 */
export function unsafeFilesystemRead(
  filePath: string,
  maxLines?: number
): { content: string; lines: number } {
  // UNSAFE: Direct path usage without validation
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  return {
    content: maxLines ? lines.slice(0, maxLines).join('\n') : content,
    lines: lines.length,
  };
}

/**
 * Example of how this can be exploited:
 * 
 * // Attacker passes: "../../../etc/passwd"
 * const result = unsafeFilesystemRead("../../../etc/passwd");
 * // Now attacker has read system files!
 */
