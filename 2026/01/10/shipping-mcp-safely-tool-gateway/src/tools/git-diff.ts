import * as path from 'path';
import { execSync } from 'child_process';
import type { PathConstraint } from '../types';
import { isPathAllowed, containsPathTraversal } from '../utils/path-validator';

/**
 * SAFE git diff wrapper
 * 
 * Validates:
 * - Repository path is within allowed directories
 * - Git commands are allow-listed
 * - No command injection
 */
export async function safeGitDiff(
  repoPath: string,
  baseRef?: string,
  headRef?: string,
  pathConstraints?: PathConstraint[],
  allowedCommands: string[] = ['git']
): Promise<{ diff: string; exitCode: number }> {
  // Validate repository path
  if (containsPathTraversal(repoPath)) {
    throw new Error('Repository path contains traversal attempt');
  }

  const normalized = path.normalize(repoPath);

  if (pathConstraints) {
    const pathCheck = isPathAllowed(normalized, pathConstraints);
    if (!pathCheck.allowed) {
      throw new Error(`Repository path validation failed: ${pathCheck.reason}`);
    }
  }

  // Check if it's a git repository
  if (!isGitRepository(normalized)) {
    throw new Error(`Not a git repository: ${normalized}`);
  }

  // Build git command safely
  const gitCommand = buildGitDiffCommand(baseRef, headRef, allowedCommands);

  try {
    // Execute git command in repository directory
    const diff = execSync(gitCommand, {
      cwd: normalized,
      maxBuffer: 10 * 1024 * 1024, // 10MB max output
      timeout: 30000, // 30 second timeout
      encoding: 'utf-8',
    });

    return {
      diff: diff.toString(),
      exitCode: 0,
    };
  } catch (error: any) {
    // Git command failed
    return {
      diff: error.stdout?.toString() || error.message || 'Git command failed',
      exitCode: error.status || 1,
    };
  }
}

/**
 * Check if path is a git repository
 */
function isGitRepository(repoPath: string): boolean {
  try {
    const gitDir = path.join(repoPath, '.git');
    const fs = require('fs');
    return fs.existsSync(gitDir) || fs.existsSync(repoPath + '/.git');
  } catch {
    return false;
  }
}

/**
 * Build git diff command safely
 */
function buildGitDiffCommand(
  baseRef?: string,
  headRef?: string,
  allowedCommands: string[] = ['git']
): string {
  // Only allow 'git' command
  if (!allowedCommands.includes('git')) {
    throw new Error('Git command not allowed');
  }

  // Build command parts
  const parts: string[] = ['git', 'diff'];

  // Add refs if provided (validate they're safe)
  if (baseRef) {
    // Validate ref doesn't contain shell injection characters
    if (!/^[a-zA-Z0-9/._-]+$/.test(baseRef)) {
      throw new Error('Invalid base ref format');
    }
    parts.push(baseRef);
  }

  if (headRef) {
    if (!/^[a-zA-Z0-9/._-]+$/.test(headRef)) {
      throw new Error('Invalid head ref format');
    }
    parts.push(headRef);
  }

  // Join with spaces (safe because we validated inputs)
  return parts.join(' ');
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
 * const result = await safeGitDiff(
 *   '/workspace/user-123/my-repo',
 *   'main',
 *   'feature-branch',
 *   constraints
 * );
 * 
 * // This fails (path traversal)
 * await safeGitDiff('../../../etc', undefined, undefined, constraints);
 * // Error: Repository path validation failed: Path not in allowed directories
 */
