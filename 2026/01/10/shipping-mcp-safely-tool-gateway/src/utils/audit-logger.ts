import * as crypto from 'crypto';
import type { AuditLog, ToolCallRequest, PolicyDecision, ExecutionResult } from '../types';

/**
 * Simple in-memory audit logger.
 * In production, this would write to immutable storage (S3, block storage, etc.)
 */
class AuditLogger {
  private logs: AuditLog[] = [];

  /**
   * Generate a unique audit ID
   */
  private generateAuditId(): string {
    return `audit-${Date.now()}-${crypto.randomBytes(8).toString('hex')}`;
  }

  /**
   * Log a tool call with policy decision and execution result
   */
  async log(
    request: ToolCallRequest,
    decision: PolicyDecision,
    executionResult: ExecutionResult,
    duration: number,
    sandboxId?: string
  ): Promise<string> {
    const auditId = this.generateAuditId();
    
    const log: AuditLog = {
      auditId,
      timestamp: new Date().toISOString(),
      userId: request.context.userId,
      workspaceId: request.context.workspaceId,
      tool: request.tool,
      arguments: this.redactSensitive(request.arguments),
      policyDecision: decision.decision,
      executionResult: executionResult.success ? 'success' : 'error',
      duration,
      sandboxId,
      error: executionResult.error,
    };

    this.logs.push(log);
    
    // In production, also write to immutable storage
    // await this.writeToImmutableStorage(log);
    
    console.log(`[AUDIT] ${JSON.stringify(log)}`);
    
    return auditId;
  }

  /**
   * Redact sensitive information from arguments
   */
  private redactSensitive(args: Record<string, unknown>): Record<string, unknown> {
    const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'auth'];
    const redacted = { ...args };
    
    for (const key of Object.keys(redacted)) {
      if (sensitiveKeys.some(sk => key.toLowerCase().includes(sk))) {
        redacted[key] = '[REDACTED]';
      }
    }
    
    return redacted;
  }

  /**
   * Query logs (for testing and debugging)
   */
  query(filters: {
    userId?: string;
    tool?: string;
    decision?: 'allow' | 'deny';
    startTime?: string;
    endTime?: string;
  }): AuditLog[] {
    return this.logs.filter(log => {
      if (filters.userId && log.userId !== filters.userId) return false;
      if (filters.tool && log.tool !== filters.tool) return false;
      if (filters.decision && log.policyDecision !== filters.decision) return false;
      if (filters.startTime && log.timestamp < filters.startTime) return false;
      if (filters.endTime && log.timestamp > filters.endTime) return false;
      return true;
    });
  }

  /**
   * Get all logs (for testing)
   */
  getAllLogs(): AuditLog[] {
    return [...this.logs];
  }

  /**
   * Clear logs (for testing)
   */
  clear(): void {
    this.logs = [];
  }
}

export const auditLogger = new AuditLogger();
