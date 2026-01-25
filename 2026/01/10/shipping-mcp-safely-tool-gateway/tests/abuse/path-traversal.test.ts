import { validateToolArguments } from '../../src/gateway/validator';
import type { PolicyConstraints } from '../../src/types';
import { safeFilesystemRead } from '../../src/tools/filesystem-read';
import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

describe('Path Traversal Defense', () => {
  const constraints: PolicyConstraints = {
    pathConstraints: [
      {
        type: 'allow',
        pattern: '/workspace/**',
        basePath: '/workspace',
      },
    ],
  };

  describe('Validator Defense', () => {
    it('should block basic path traversal', async () => {
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

    it('should block encoded path traversal', async () => {
      const result = await validateToolArguments(
        'filesystem_read',
        {
          path: '..%2F..%2Fetc%2Fpasswd', // URL encoded
        },
        constraints
      );

      // Note: URL decoding would happen before validation in production
      // This test shows the concept
      expect(result.valid).toBe(false);
    });

    it('should block absolute paths outside workspace', async () => {
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

    it('should block paths with null bytes', async () => {
      const result = await validateToolArguments(
        'filesystem_read',
        {
          path: '/workspace/file.txt\0../../../etc/passwd',
        },
        constraints
      );

      expect(result.valid).toBe(false);
    });
  });

  describe('Tool Wrapper Defense', () => {
    let tempDir: string;
    let workspaceDir: string;

    beforeEach(() => {
      // Create temporary workspace structure
      tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'test-workspace-'));
      workspaceDir = path.join(tempDir, 'workspace');
      fs.mkdirSync(workspaceDir, { recursive: true });

      // Create a test file
      const testFile = path.join(workspaceDir, 'test.txt');
      fs.writeFileSync(testFile, 'test content');
    });

    afterEach(() => {
      // Cleanup
      fs.rmSync(tempDir, { recursive: true, force: true });
    });

    it('should allow reading file within workspace', async () => {
      const testPath = path.join(workspaceDir, 'test.txt');
      const pathConstraints = [
        {
          type: 'allow',
          pattern: '**',
          basePath: workspaceDir,
        },
      ];

      const result = await safeFilesystemRead(testPath, undefined, pathConstraints);

      expect(result.content).toBe('test content');
    });

    it('should block path traversal attempt', async () => {
      const pathConstraints = [
        {
          type: 'allow',
          pattern: '**',
          basePath: workspaceDir,
        },
      ];

      // Try to escape workspace
      const maliciousPath = path.join(workspaceDir, '..', '..', 'etc', 'passwd');

      await expect(
        safeFilesystemRead(maliciousPath, undefined, pathConstraints)
      ).rejects.toThrow('traversal');
    });

    it('should block reading file outside workspace', async () => {
      const pathConstraints = [
        {
          type: 'allow',
          pattern: '**',
          basePath: workspaceDir,
        },
      ];

      // Try to read from system directory
      const systemPath = '/etc/passwd';

      await expect(
        safeFilesystemRead(systemPath, undefined, pathConstraints)
      ).rejects.toThrow('not in allowed directories');
    });
  });
});
