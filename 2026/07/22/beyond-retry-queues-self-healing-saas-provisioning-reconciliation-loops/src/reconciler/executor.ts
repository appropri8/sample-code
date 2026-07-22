import { ProvisioningAction, ProvisioningResult } from '../providers/interfaces';
import { createProviders } from '../providers/factory';
import { RetryableError, TerminalError } from './errors';
import { idempotencyKeyFor } from '../utils/idempotency';

export class Executor {
  private providers = createProviders();

  async execute(action: ProvisioningAction): Promise<ProvisioningResult> {
    const provider = this.providers[action.provider as keyof typeof this.providers];
    if (!provider) {
      throw new TerminalError(`Unknown provider: ${action.provider}`, 'Fix provider configuration');
    }

    // Idempotency check
    const existing = await idempotencyKeyFor(action.idempotencyKey);
    if (existing) {
      if (action.type.startsWith('create_')) {
        return {
          success: true,
          externalResourceId: existing.externalResourceId,
          alreadyExists: true,
        };
      }
    }

    const result = await provider.execute(action);

    if (result.success) {
      await idempotencyKeyFor(action.idempotencyKey, action.provider, result.externalResourceId!);
    }

    if (result.error && this.isTerminal(result.error)) {
      throw new TerminalError(result.error, 'Update tenant configuration and increment generation');
    }

    if (!result.success && !this.isRetryable(result.error)) {
      throw new TerminalError(result.error, 'Contact support with idempotency key');
    }

    return result;
  }

  private isRetryable(error?: string): boolean {
    if (!error) return true;
    const retryablePatterns = ['timeout', 'network', '429', '503', '502', '500'];
    return retryablePatterns.some(p => error.toLowerCase().includes(p));
  }

  private isTerminal(error?: string): boolean {
    if (!error) return false;
    const terminalPatterns = ['400', '401', '403', '404', 'invalid_plan', 'quota_exceeded'];
    return terminalPatterns.some(p => error.toLowerCase().includes(p));
  }
}