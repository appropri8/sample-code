/**
 * A/B testing and shadow testing for LLM systems.
 */

import * as crypto from 'crypto';

export interface ExperimentAssignment {
  variant: 'baseline' | 'candidate';
  cohort: 'control' | 'treatment';
  experiment_name: string;
}

export function assignVariant(
  userId: string,
  experimentName: string,
  splitRatio: number = 0.5
): 'baseline' | 'candidate' {
  const seed = `${experimentName}:${userId}`;
  const hashValue = parseInt(
    crypto.createHash('md5').update(seed).digest('hex'),
    16
  );
  const threshold = Math.floor(splitRatio * 100);
  return hashValue % 100 < threshold ? 'candidate' : 'baseline';
}

export function assignCohort(
  userId: string,
  experimentName: string
): 'control' | 'treatment' {
  const variant = assignVariant(userId, experimentName);
  return variant === 'candidate' ? 'treatment' : 'control';
}

export class ABTest {
  constructor(
    private experimentName: string,
    private baselineModel: (query: string) => string,
    private candidateModel: (query: string) => string,
    private splitRatio: number = 0.5
  ) {}

  run(
    userId: string,
    query: string
  ): [string, ExperimentAssignment] {
    const assignment: ExperimentAssignment = {
      variant: assignVariant(userId, this.experimentName, this.splitRatio),
      cohort: assignCohort(userId, this.experimentName),
      experiment_name: this.experimentName,
    };

    const output =
      assignment.variant === 'baseline'
        ? this.baselineModel(query)
        : this.candidateModel(query);

    return [output, assignment];
  }
}

export class ShadowTest {
  constructor(
    private experimentName: string,
    private baselineModel: (query: string) => string,
    private candidateModel: (query: string) => string,
    private logger?: (comparison: any) => void
  ) {}

  run(
    userId: string,
    query: string
  ): [string, any] {
    // User sees baseline
    const baselineOutput = this.baselineModel(query);

    // Candidate runs in background (user doesn't see this)
    const candidateOutput = this.candidateModel(query);

    // Log comparison
    const comparisonData = {
      experiment_name: this.experimentName,
      user_id: userId,
      query,
      baseline_output: baselineOutput,
      candidate_output: candidateOutput,
    };

    if (this.logger) {
      this.logger(comparisonData);
    }

    return [baselineOutput, comparisonData];
  }
}

