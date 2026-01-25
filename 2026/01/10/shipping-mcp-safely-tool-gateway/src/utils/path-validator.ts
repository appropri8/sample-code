import * as path from 'path';
import type { PathConstraint } from '../types';

/**
 * Validates that a file path is within allowed directories.
 * Prevents path traversal attacks.
 */
export function isPathAllowed(
  filePath: string,
  constraints: PathConstraint[]
): { allowed: boolean; reason?: string } {
  // Normalize the path to prevent traversal
  const normalized = path.normalize(filePath);
  
  // Resolve to absolute path if relative
  const absolute = path.isAbsolute(normalized)
    ? normalized
    : path.resolve(normalized);

  // Check against each constraint
  for (const constraint of constraints) {
    if (constraint.type === 'deny') {
      // Check if path matches deny pattern
      if (matchesPattern(absolute, constraint.pattern, constraint.basePath)) {
        return {
          allowed: false,
          reason: `Path matches deny pattern: ${constraint.pattern}`,
        };
      }
    } else if (constraint.type === 'allow') {
      // Check if path is within allowed base path
      const basePath = path.resolve(constraint.basePath);
      if (absolute.startsWith(basePath)) {
        // Check if it matches the pattern
        if (matchesPattern(absolute, constraint.pattern, constraint.basePath)) {
          return { allowed: true };
        }
      }
    }
  }

  // Default deny if no allow constraint matched
  return {
    allowed: false,
    reason: 'Path not in allowed directories',
  };
}

/**
 * Simple glob pattern matching (supports ** for recursive)
 */
function matchesPattern(
  filePath: string,
  pattern: string,
  basePath: string
): boolean {
  // Convert glob pattern to regex
  const base = path.resolve(basePath);
  const relativePath = path.relative(base, filePath);
  
  // Convert glob to regex
  let regexPattern = pattern
    .replace(/\*\*/g, '.*') // ** matches any path
    .replace(/\*/g, '[^/]*') // * matches any filename
    .replace(/\?/g, '.'); // ? matches single char

  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(relativePath);
}

/**
 * Checks for path traversal attempts in a path string.
 */
export function containsPathTraversal(filePath: string): boolean {
  const normalized = path.normalize(filePath);
  
  // Check for parent directory references
  if (normalized.includes('..')) {
    return true;
  }
  
  // Check for absolute paths that escape base
  if (path.isAbsolute(normalized)) {
    // In a gateway, we typically want relative paths within a workspace
    // Absolute paths might be an attempt to escape
    return true;
  }
  
  return false;
}
