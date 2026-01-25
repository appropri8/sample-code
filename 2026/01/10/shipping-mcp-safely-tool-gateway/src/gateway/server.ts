import express from 'express';
import type { ToolCallRequest, ToolCallResponse } from '../types';
import { validateToolArguments } from './validator';
import { evaluatePolicy } from './policy-engine';
import { sandboxExecutor } from './sandbox';
import { auditLogger } from '../utils/audit-logger';
import { safeFilesystemRead } from '../tools/filesystem-read';
import { safeGitDiff } from '../tools/git-diff';
import { loadPolicies } from './policy-engine';
import { defaultPolicies } from '../policies/default-policy';

const app = express();
app.use(express.json());

// Load default policies
loadPolicies(defaultPolicies);

/**
 * Main tool call endpoint
 */
app.post('/api/tools/call', async (req, res) => {
  const startTime = Date.now();
  const request: ToolCallRequest = req.body;

  try {
    // Validate request structure
    if (!request.tool || !request.arguments || !request.context) {
      return res.status(400).json({
        success: false,
        error: 'Invalid request: missing tool, arguments, or context',
        auditId: 'invalid-request',
      } as ToolCallResponse);
    }

    // Get policy for tool
    const policyDecision = await evaluatePolicy(request.tool, request.context);

    if (policyDecision.decision !== 'allow') {
      const auditId = await auditLogger.log(
        request,
        policyDecision,
        { success: false, error: policyDecision.reason },
        Date.now() - startTime
      );

      return res.status(403).json({
        success: false,
        error: policyDecision.reason || 'Policy denied',
        auditId,
      } as ToolCallResponse);
    }

    // Validate tool arguments
    const validation = await validateToolArguments(
      request.tool,
      request.arguments,
      policyDecision.sandboxConfig
        ? {
            // Get constraints from policy (simplified for example)
            pathConstraints: [
              {
                type: 'allow',
                pattern: '/workspace/**',
                basePath: '/workspace',
              },
            ],
          }
        : undefined
    );

    if (!validation.valid) {
      const auditId = await auditLogger.log(
        request,
        { decision: 'deny', reason: 'Validation failed' },
        { success: false, error: validation.errors?.join(', ') },
        Date.now() - startTime
      );

      return res.status(400).json({
        success: false,
        error: `Validation failed: ${validation.errors?.join(', ')}`,
        auditId,
      } as ToolCallResponse);
    }

    // Execute in sandbox (simulated)
    const sandboxResult = await sandboxExecutor.execute(
      request.tool,
      request.arguments,
      policyDecision.sandboxConfig
    );

    if (!sandboxResult.success) {
      const auditId = await auditLogger.log(
        request,
        policyDecision,
        { success: false, error: sandboxResult.error },
        Date.now() - startTime,
        sandboxResult.exitCode?.toString()
      );

      return res.status(500).json({
        success: false,
        error: sandboxResult.error || 'Sandbox execution failed',
        auditId,
      } as ToolCallResponse);
    }

    // Execute actual tool (after sandbox validation)
    let toolResult: unknown;
    let executionError: string | undefined;

    try {
      switch (request.tool) {
        case 'filesystem_read':
          toolResult = await safeFilesystemRead(
            request.arguments.path as string,
            request.arguments.maxLines as number | undefined,
            [
              {
                type: 'allow',
                pattern: '/workspace/**',
                basePath: '/workspace',
              },
            ]
          );
          break;

        case 'git_diff':
          toolResult = await safeGitDiff(
            request.arguments.repoPath as string,
            request.arguments.baseRef as string | undefined,
            request.arguments.headRef as string | undefined,
            [
              {
                type: 'allow',
                pattern: '/workspace/**',
                basePath: '/workspace',
              },
            ]
          );
          break;

        default:
          executionError = `Tool not implemented: ${request.tool}`;
      }
    } catch (error) {
      executionError =
        error instanceof Error ? error.message : 'Unknown error';
    }

    const executionResult = {
      success: !executionError,
      output: toolResult,
      error: executionError,
      exitCode: executionError ? 1 : 0,
    };

    // Log audit
    const auditId = await auditLogger.log(
      request,
      policyDecision,
      executionResult,
      Date.now() - startTime,
      sandboxResult.exitCode?.toString()
    );

    if (executionError) {
      return res.status(500).json({
        success: false,
        error: executionError,
        auditId,
      } as ToolCallResponse);
    }

    return res.json({
      success: true,
      result: toolResult,
      auditId,
    } as ToolCallResponse);
  } catch (error) {
    const auditId = await auditLogger.log(
      request,
      { decision: 'deny', reason: 'Internal error' },
      {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      Date.now() - startTime
    );

    return res.status(500).json({
      success: false,
      error: 'Internal server error',
      auditId,
    } as ToolCallResponse);
  }
});

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

/**
 * Get audit logs (for testing/debugging)
 */
app.get('/api/audit', (req, res) => {
  const logs = auditLogger.query({
    userId: req.query.userId as string | undefined,
    tool: req.query.tool as string | undefined,
    decision: req.query.decision as 'allow' | 'deny' | undefined,
  });

  res.json({ logs });
});

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  console.log(`[GATEWAY] Server running on http://localhost:${PORT}`);
  console.log(`[GATEWAY] Health check: http://localhost:${PORT}/health`);
  console.log(`[GATEWAY] Tool call endpoint: http://localhost:${PORT}/api/tools/call`);
});
