import {
  loadPolicy,
  evaluatePolicy,
  clearPolicies,
  getPolicy,
} from '../../src/gateway/policy-engine';
import type { Policy, ToolCallContext } from '../../src/types';

describe('Policy Engine', () => {
  beforeEach(() => {
    clearPolicies();
  });

  describe('Role-Based Access', () => {
    it('should allow tool call for allowed role', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer', 'analyst'],
        constraints: {},
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
        userRole: 'developer',
      };

      const decision = await evaluatePolicy('filesystem_read', context);

      expect(decision.decision).toBe('allow');
    });

    it('should deny tool call for disallowed role', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer'],
        constraints: {},
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
        userRole: 'analyst', // Not in allowed roles
      };

      const decision = await evaluatePolicy('filesystem_read', context);

      expect(decision.decision).toBe('deny');
      expect(decision.reason).toContain('not allowed');
    });

    it('should deny if tool not found', async () => {
      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
      };

      const decision = await evaluatePolicy('unknown_tool', context);

      expect(decision.decision).toBe('deny');
      expect(decision.reason).toContain('not found');
    });
  });

  describe('Workspace Restrictions', () => {
    it('should allow tool call for allowed workspace', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer'],
        allowedWorkspaces: ['workspace-456', 'workspace-789'],
        constraints: {},
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
        userRole: 'developer',
      };

      const decision = await evaluatePolicy('filesystem_read', context);

      expect(decision.decision).toBe('allow');
    });

    it('should deny tool call for disallowed workspace', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer'],
        allowedWorkspaces: ['workspace-456'],
        constraints: {},
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-999', // Not in allowed workspaces
        sessionId: 'session-789',
        userRole: 'developer',
      };

      const decision = await evaluatePolicy('filesystem_read', context);

      expect(decision.decision).toBe('deny');
      expect(decision.reason).toContain('not allowed');
    });
  });

  describe('Rate Limiting', () => {
    it('should allow within rate limit', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer'],
        constraints: {
          rateLimit: {
            perUser: {
              requests: 10,
              window: 60000, // 1 minute
            },
          },
        },
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
        userRole: 'developer',
      };

      // Make 5 calls (within limit)
      for (let i = 0; i < 5; i++) {
        const decision = await evaluatePolicy('filesystem_read', context);
        expect(decision.decision).toBe('allow');
      }
    });

    it('should deny when rate limit exceeded', async () => {
      const policy: Policy = {
        tool: 'filesystem_read',
        allowedRoles: ['developer'],
        constraints: {
          rateLimit: {
            perUser: {
              requests: 3,
              window: 60000,
            },
          },
        },
      };

      loadPolicy(policy);

      const context: ToolCallContext = {
        userId: 'user-123',
        workspaceId: 'workspace-456',
        sessionId: 'session-789',
        userRole: 'developer',
      };

      // Make 3 calls (at limit)
      for (let i = 0; i < 3; i++) {
        const decision = await evaluatePolicy('filesystem_read', context);
        expect(decision.decision).toBe('allow');
      }

      // 4th call should be denied
      const decision = await evaluatePolicy('filesystem_read', context);
      expect(decision.decision).toBe('deny');
      expect(decision.reason).toContain('Rate limit exceeded');
    });
  });

  describe('Policy Management', () => {
    it('should load and retrieve policy', () => {
      const policy: Policy = {
        tool: 'test_tool',
        allowedRoles: ['developer'],
        constraints: {},
      };

      loadPolicy(policy);

      const retrieved = getPolicy('test_tool');
      expect(retrieved).toEqual(policy);
    });
  });
});
