/** Canary deployment for gradual rollout */
import { Workflow } from "../workflow";

export interface CanaryMetrics {
  canary_requests: number;
  canary_errors: number;
  canary_latency_sum: number;
  canary_cost_sum: number;
  baseline_requests: number;
  baseline_errors: number;
  baseline_latency_sum: number;
  baseline_cost_sum: number;
}

export interface RollbackConditions {
  error_rate_threshold: number;
  latency_threshold_ms: number;
  cost_threshold_multiplier: number;
}

export class CanaryDeployment {
  baseline: Workflow;
  candidate: Workflow;
  canaryPct: number;
  rollbackConditions: RollbackConditions;
  metrics: CanaryMetrics;
  rolledBack: boolean;

  constructor(
    baselineWorkflow: Workflow,
    candidateWorkflow: Workflow,
    canaryPercentage: number = 0.01,
    rollbackConditions?: RollbackConditions
  ) {
    this.baseline = baselineWorkflow;
    this.candidate = candidateWorkflow;
    this.canaryPct = canaryPercentage;
    this.rollbackConditions = rollbackConditions || {
      error_rate_threshold: 0.05,
      latency_threshold_ms: 10000,
      cost_threshold_multiplier: 2.0
    };
    this.metrics = {
      canary_requests: 0,
      canary_errors: 0,
      canary_latency_sum: 0,
      canary_cost_sum: 0,
      baseline_requests: 0,
      baseline_errors: 0,
      baseline_latency_sum: 0,
      baseline_cost_sum: 0
    };
    this.rolledBack = false;
  }

  async route(input: Record<string, any>): Promise<Record<string, any>> {
    if (this.rolledBack) {
      return this.baseline.execute(input);
    }

    const useCanary = Math.random() < this.canaryPct;

    if (useCanary) {
      return this.runCanary(input);
    } else {
      return this.runBaseline(input);
    }
  }

  private async runBaseline(input: Record<string, any>): Promise<Record<string, any>> {
    try {
      const result = await this.baseline.execute(input);
      this.metrics.baseline_requests++;
      this.metrics.baseline_latency_sum += result.latency_ms || 0;
      this.metrics.baseline_cost_sum += result.cost || 0;
      return result;
    } catch (error) {
      this.metrics.baseline_errors++;
      throw error;
    }
  }

  private async runCanary(input: Record<string, any>): Promise<Record<string, any>> {
    try {
      const result = await this.candidate.execute(input);

      this.metrics.canary_requests++;
      this.metrics.canary_latency_sum += result.latency_ms || 0;
      this.metrics.canary_cost_sum += result.cost || 0;

      if (this.shouldRollback()) {
        this.rolledBack = true;
        return this.baseline.execute(input);
      }

      return result;
    } catch (error) {
      this.metrics.canary_errors++;

      if (this.shouldRollback()) {
        this.rolledBack = true;
        return this.baseline.execute(input);
      }

      throw error;
    }
  }

  private shouldRollback(): boolean {
    if (this.metrics.canary_requests < 10) {
      return false;
    }

    const errorRate = this.metrics.canary_errors / this.metrics.canary_requests;
    if (errorRate > this.rollbackConditions.error_rate_threshold) {
      return true;
    }

    if (this.metrics.canary_requests > 0) {
      const avgLatency = this.metrics.canary_latency_sum / this.metrics.canary_requests;
      if (avgLatency > this.rollbackConditions.latency_threshold_ms) {
        return true;
      }

      if (this.metrics.baseline_requests > 0) {
        const baselineAvgCost = this.metrics.baseline_cost_sum / this.metrics.baseline_requests;
        const canaryAvgCost = this.metrics.canary_cost_sum / this.metrics.canary_requests;
        if (baselineAvgCost > 0) {
          const costMultiplier = canaryAvgCost / baselineAvgCost;
          if (costMultiplier > this.rollbackConditions.cost_threshold_multiplier) {
            return true;
          }
        }
      }
    }

    return false;
  }

  getMetrics() {
    return {
      canary: {
        requests: this.metrics.canary_requests,
        errors: this.metrics.canary_errors,
        error_rate: this.metrics.canary_requests > 0
          ? this.metrics.canary_errors / this.metrics.canary_requests
          : 0,
        avg_latency_ms: this.metrics.canary_requests > 0
          ? this.metrics.canary_latency_sum / this.metrics.canary_requests
          : 0,
        avg_cost: this.metrics.canary_requests > 0
          ? this.metrics.canary_cost_sum / this.metrics.canary_requests
          : 0
      },
      baseline: {
        requests: this.metrics.baseline_requests,
        errors: this.metrics.baseline_errors,
        error_rate: this.metrics.baseline_requests > 0
          ? this.metrics.baseline_errors / this.metrics.baseline_requests
          : 0,
        avg_latency_ms: this.metrics.baseline_requests > 0
          ? this.metrics.baseline_latency_sum / this.metrics.baseline_requests
          : 0,
        avg_cost: this.metrics.baseline_requests > 0
          ? this.metrics.baseline_cost_sum / this.metrics.baseline_requests
          : 0
      },
      rolled_back: this.rolledBack
    };
  }
}

