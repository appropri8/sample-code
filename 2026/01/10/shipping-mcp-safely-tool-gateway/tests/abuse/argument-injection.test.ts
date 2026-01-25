import { validateToolArguments } from '../../src/gateway/validator';
import type { PolicyConstraints } from '../../src/types';
import { safeGitDiff } from '../../src/tools/git-diff';

describe('Argument Injection Defense', () => {
  describe('Command Injection', () => {
    it('should reject command injection in git arguments', async () => {
      // This test demonstrates the concept
      // In a real implementation, git_diff would validate refs more strictly

      const pathConstraints = [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ];

      // Attempt command injection via ref name
      const maliciousRef = "main; rm -rf /";

      // The safeGitDiff function validates ref format
      await expect(
        safeGitDiff(
          '/workspace/repo',
          maliciousRef,
          undefined,
          pathConstraints
        )
      ).rejects.toThrow('Invalid base ref format');
    });

    it('should reject shell metacharacters in paths', async () => {
      const constraints: PolicyConstraints = {
        pathConstraints: [
          {
            type: 'allow',
            pattern: '/workspace/**',
            basePath: '/workspace',
          },
        ],
      };

      // Attempt injection via path
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/file.txt; rm -rf /',
      }, constraints);

      // Path pattern validation should catch this
      expect(result.valid).toBe(false);
    });
  });

  describe('JSON Schema Validation', () => {
    it('should reject extra fields that might be used for injection', async () => {
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/file.txt',
        __proto__: { malicious: true }, // Prototype pollution attempt
        constructor: { malicious: true },
      });

      // Strict schema should reject extra fields
      expect(result.valid).toBe(false);
    });

    it('should enforce type constraints strictly', async () => {
      const result = await validateToolArguments('filesystem_read', {
        path: '/workspace/file.txt',
        maxLines: '100', // Should be number, not string
      });

      expect(result.valid).toBe(false);
      expect(result.errors).toBeDefined();
    });
  });

  describe('Path Pattern Validation', () => {
    const constraints: PolicyConstraints = {
      pathConstraints: [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ],
    };

    it('should reject paths with shell metacharacters', async () => {
      const maliciousPaths = [
        '/workspace/file.txt; cat /etc/passwd',
        '/workspace/file.txt | cat /etc/passwd',
        '/workspace/file.txt && rm -rf /',
        '/workspace/file.txt || echo hacked',
        '/workspace/file.txt `whoami`',
        '/workspace/file.txt $(whoami)',
      ];

      for (const maliciousPath of maliciousPaths) {
        const result = await validateToolArguments('filesystem_read', {
          path: maliciousPath,
        }, constraints);

        // Path pattern should reject these
        expect(result.valid).toBe(false);
      }
    });
  });
});
