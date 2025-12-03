/**
 * Logging module for LLM calls.
 * Captures input, output, metadata, and performance metrics.
 */

import * as crypto from 'crypto';

export interface LLMLog {
  request_id: string;
  timestamp: string;
  user_id_hash: string;
  session_id?: string;
  input?: {
    query: string;
    context?: string[];
  };
  output?: {
    text: string;
    tokens_used?: number;
  };
  model?: {
    name: string;
    version: string;
    temperature?: number;
  };
  prompt?: {
    template_version: string;
    template_hash: string;
  };
  performance?: {
    latency_ms: number;
    cost_usd: number;
  };
  experiment?: {
    variant: string;
    cohort: string;
  };
  feedback?: {
    thumbs_up?: boolean;
    rating?: number;
    labels?: Record<string, string>;
    timestamp: string;
  };
}

function redactPII(text: string): string {
  // Email addresses
  text = text.replace(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, '[EMAIL]');
  // Phone numbers
  text = text.replace(/\b\d{3}-\d{3}-\d{4}\b/g, '[PHONE]');
  // Credit cards
  text = text.replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[CARD]');
  return text;
}

function hashUserId(userId: string): string {
  return crypto.createHash('sha256').update(userId).digest('hex').substring(0, 16);
}

export class LLMLogger {
  private logs: LLMLog[] = [];
  private logFile?: string;
  private redactPIIEnabled: boolean;

  constructor(logFile?: string, redactPIIEnabled: boolean = true) {
    this.logFile = logFile;
    this.redactPIIEnabled = redactPIIEnabled;
  }

  logCall(params: {
    request_id: string;
    user_id: string;
    query: string;
    response: string;
    model_name: string;
    model_version: string;
    prompt_version: string;
    latency_ms: number;
    tokens_used: number;
    cost_usd: number;
    session_id?: string;
    context?: string[];
    experiment_variant?: string;
    experiment_cohort?: string;
    temperature?: number;
  }): LLMLog {
    const {
      request_id,
      user_id,
      query,
      response,
      model_name,
      model_version,
      prompt_version,
      latency_ms,
      tokens_used,
      cost_usd,
      session_id,
      context,
      experiment_variant,
      experiment_cohort,
      temperature = 0.7,
    } = params;

    // Redact PII if enabled
    const queryRedacted = this.redactPIIEnabled ? redactPII(query) : query;
    const responseRedacted = this.redactPIIEnabled ? redactPII(response) : response;

    // Hash user ID
    const userIdHash = hashUserId(user_id);

    // Create log record
    const log: LLMLog = {
      request_id,
      timestamp: new Date().toISOString(),
      user_id_hash: userIdHash,
      session_id,
      input: {
        query: queryRedacted,
        context: context || [],
      },
      output: {
        text: responseRedacted,
        tokens_used,
      },
      model: {
        name: model_name,
        version: model_version,
        temperature,
      },
      prompt: {
        template_version: prompt_version,
        template_hash: crypto
          .createHash('md5')
          .update(prompt_version)
          .digest('hex')
          .substring(0, 8),
      },
      performance: {
        latency_ms,
        cost_usd,
      },
      experiment:
        experiment_variant
          ? {
              variant: experiment_variant || 'baseline',
              cohort: experiment_cohort || 'control',
            }
          : undefined,
    };

    // Store log
    this.logs.push(log);

    // Write to file if specified (in Node.js environment)
    if (this.logFile && typeof require !== 'undefined') {
      const fs = require('fs');
      fs.appendFileSync(this.logFile, JSON.stringify(log) + '\n');
    }

    return log;
  }

  addFeedback(
    request_id: string,
    feedback: {
      thumbs_up?: boolean;
      rating?: number;
      labels?: Record<string, string>;
    }
  ): void {
    for (const log of this.logs) {
      if (log.request_id === request_id) {
        log.feedback = {
          ...feedback,
          timestamp: new Date().toISOString(),
        };
        break;
      }
    }
  }

  getLogs(filters?: {
    user_id_hash?: string;
    variant?: string;
  }): LLMLog[] {
    let logs = this.logs;
    if (filters?.user_id_hash) {
      logs = logs.filter((l) => l.user_id_hash === filters.user_id_hash);
    }
    if (filters?.variant) {
      logs = logs.filter(
        (l) => l.experiment?.variant === filters.variant
      );
    }
    return logs;
  }
}

