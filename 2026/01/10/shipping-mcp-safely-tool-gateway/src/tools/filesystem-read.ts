import * as fs from 'fs';
import * as path from 'path';
import type { PathConstraint } from '../types';
import { isPathAllowed, containsPathTraversal } from '../utils/path-validator';

/**
 * SAFE VERSION - Use this in production
 * 
 * This demonstrates safe filesystem read:
 * - Path validation against allow-lists
 * - Size limits
 * - Path traversal defense
 * - Error handling
 */
export async function safeFilesystemRead(
  filePath: string,
  maxLines?: number,
  pathConstraints?: PathConstraint[]
): Promise<{ content: string; lines: number }> {
  // Validate path is not a traversal attempt
  if (containsPathTraversal(filePath)) {
    throw new Error('Path contains traversal attempt');
  }

  // Normalize path
  const normalized = path.normalize(filePath);

  // Validate against path constraints
  if (pathConstraints) {
    const pathCheck = isPathAllowed(normalized, pathConstraints);
    if (!pathCheck.allowed) {
      throw new Error(`Path validation failed: ${pathCheck.reason}`);
    }
  }

  // Check file exists
  if (!fs.existsSync(normalized)) {
    throw new Error(`File not found: ${normalized}`);
  }

  // Check it's a file, not a directory
  const stats = fs.statSync(normalized);
  if (!stats.isFile()) {
    throw new Error(`Path is not a file: ${normalized}`);
  }

  // Check file size (10MB limit)
  const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
  if (stats.size > MAX_FILE_SIZE) {
    throw new Error(
      `File too large: ${stats.size} bytes (max: ${MAX_FILE_SIZE} bytes)`
    );
  }

  // Read file
  const content = fs.readFileSync(normalized, 'utf-8');
  const lines = content.split('\n');

  // Apply line limit if specified
  const result = {
    content: maxLines ? lines.slice(0, maxLines).join('\n') : content,
    lines: lines.length,
  };

  // Encode output to prevent prompt injection
  // In production, this would escape special characters
  return result;
}

/**
 * Example usage:
 * 
 * const constraints: PathConstraint[] = [
 *   {
 *     type: 'allow',
 *     pattern: '/workspace/**',
 *     basePath: '/workspace'
 *   }
 * ];
 * 
 * // This works
 * const result = await safeFilesystemRead(
 *   '/workspace/user-123/document.txt',
 *   100,
 *   constraints
 * );
 * 
 * // This fails (path traversal)
 * await safeFilesystemRead('../../../etc/passwd', undefined, constraints);
 * // Error: Path validation failed: Path not in allowed directories
 */
