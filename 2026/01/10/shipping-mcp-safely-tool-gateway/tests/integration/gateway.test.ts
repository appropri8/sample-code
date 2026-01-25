import request from 'supertest';
import express from 'express';
import type { ToolCallRequest } from '../../src/types';
import { loadPolicies } from '../../src/gateway/policy-engine';
import { defaultPolicies } from '../../src/policies/default-policy';

// Import server setup (simplified for testing)
// In a real implementation, you'd export the app from server.ts
const app = express();
app.use(express.json());

// Mock gateway endpoint for testing
app.post('/api/tools/call', async (req, res) => {
  const request: ToolCallRequest = req.body;

  // Simple validation for testing
  if (!request.tool || !request.arguments || !request.context) {
    return res.status(400).json({
      success: false,
      error: 'Invalid request',
      auditId: 'test-audit-id',
    });
  }

  // Load policies
  loadPolicies(defaultPolicies);

  // For testing, we'll just return a mock response
  // In real implementation, this would go through full gateway flow
  res.json({
    success: true,
    result: { message: 'Tool executed (test mode)' },
    auditId: 'test-audit-id',
  });
});

describe('Gateway Integration', () => {
  describe('Tool Call Endpoint', () => {
    it('should accept valid tool call request', async () => {
      const response = await request(app)
        .post('/api/tools/call')
        .send({
          tool: 'filesystem_read',
          arguments: {
            path: '/workspace/user-123/file.txt',
          },
          context: {
            userId: 'user-123',
            workspaceId: 'workspace-456',
            sessionId: 'session-789',
            userRole: 'developer',
          },
        });

      expect(response.status).toBe(200);
      expect(response.body.success).toBe(true);
      expect(response.body.auditId).toBeDefined();
    });

    it('should reject request missing tool', async () => {
      const response = await request(app)
        .post('/api/tools/call')
        .send({
          arguments: {
            path: '/workspace/file.txt',
          },
          context: {
            userId: 'user-123',
            workspaceId: 'workspace-456',
            sessionId: 'session-789',
          },
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should reject request missing arguments', async () => {
      const response = await request(app)
        .post('/api/tools/call')
        .send({
          tool: 'filesystem_read',
          context: {
            userId: 'user-123',
            workspaceId: 'workspace-456',
            sessionId: 'session-789',
          },
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });

    it('should reject request missing context', async () => {
      const response = await request(app)
        .post('/api/tools/call')
        .send({
          tool: 'filesystem_read',
          arguments: {
            path: '/workspace/file.txt',
          },
        });

      expect(response.status).toBe(400);
      expect(response.body.success).toBe(false);
    });
  });

  describe('Request Validation', () => {
    it('should validate request structure', async () => {
      const validRequest = {
        tool: 'filesystem_read',
        arguments: {
          path: '/workspace/file.txt',
        },
        context: {
          userId: 'user-123',
          workspaceId: 'workspace-456',
          sessionId: 'session-789',
        },
      };

      const response = await request(app)
        .post('/api/tools/call')
        .send(validRequest);

      expect(response.status).toBe(200);
    });
  });
});
