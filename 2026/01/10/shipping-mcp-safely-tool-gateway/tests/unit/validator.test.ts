import { validateToolArguments } from '../../src/gateway/validator';
import type { PolicyConstraints } from '../../src/types';

describe('Validator', () => {
  describe('JSON Schema Validation', () => {
    it('should validate correct filesystem_read arguments', async () => {
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/user-123/file.txt',
        maxLines: 100,
      });

      expect(result.valid).toBe(true);
      expect(result.errors).toBeUndefined();
    });

    it('should reject missing required field', async () => {
      const result = await validateToolArguments('filesystem_read', {
        maxLines: 100,
        // path is missing
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toContainEqual(
        expect.stringContaining('required')
      );
    });

    it('should reject invalid type', async () => {
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/file.txt',
        maxLines: 'not-a-number', // Should be number
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
    });

    it('should reject extra fields', async () => {
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/file.txt',
        extraField: 'not-allowed',
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
    });
  });

  describe('Path Validation', () => {
    const constraints: PolicyConstraints = {
      pathConstraints: [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ],
    };

    it('should allow valid path within workspace', async () => {
      const result = await validateToolArguments(
        'filesystem_read',
        {
          path: '/workspace/user-123/document.txt',
        },
        constraints
      );

      expect(result.valid).toBe(true);
    });

    it('should reject path traversal attempt', async () => {
      const result = await validateToolArguments(
        'filesystem_read',
        {
          path: '../../../etc/passwd',
        },
        constraints
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContainEqual(
        expect.stringContaining('traversal')
      );
    });

    it('should reject path outside allowed directory', async () => {
      const result = await validateToolArguments(
        'filesystem_read',
        {
          path: '/etc/passwd',
        },
        constraints
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContainEqual(
        expect.stringContaining('not in allowed directories')
      );
    });
  });

  describe('Command Allow-List', () => {
    const constraints: PolicyConstraints = {
      allowedCommands: ['git', 'ls', 'cat'],
    };

    it('should allow allowed command', async () => {
      const result = await validateToolArguments(
        'git_diff',
        {
          repoPath: '/workspace/repo',
          command: 'git',
        },
        constraints
      );

      // Note: git_diff schema doesn't have 'command' field, so this is just testing the concept
      // In a real implementation, you'd validate command separately
      expect(result.valid).toBe(true);
    });
  });

  describe('File Size Validation', () => {
    const constraints: PolicyConstraints = {
      maxFileSize: 1024, // 1KB
    };

    it('should reject content exceeding max size', async () => {
      const largeContent = 'x'.repeat(2048); // 2KB

      const result = await validateToolArguments(
        'filesystem_write',
        {
          path: '/workspace/file.txt',
          content: largeContent,
        },
        constraints
      );

      expect(result.valid).toBe(false);
      expect(result.errors).toContainEqual(
        expect.stringContaining('too large')
      );
    });
  });
});
