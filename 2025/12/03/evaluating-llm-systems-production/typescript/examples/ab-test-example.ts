/**
 * Example: A/B testing and shadow testing.
 */

import { ABTest, ShadowTest } from '../src/experiments';

function baselineModel(query: string): string {
  return `Baseline response to: ${query}`;
}

function candidateModel(query: string): string {
  return `Improved candidate response to: ${query}`;
}

function shadowLogger(comparisonData: any): void {
  console.log('Shadow test comparison logged:');
  console.log(`  User: ${comparisonData.user_id}`);
  console.log(`  Query: ${comparisonData.query}`);
  console.log(`  Baseline: ${comparisonData.baseline_output.substring(0, 50)}...`);
  console.log(`  Candidate: ${comparisonData.candidate_output.substring(0, 50)}...`);
  console.log();
}

function main() {
  // A/B Test Example
  console.log('='.repeat(60));
  console.log('A/B Test Example');
  console.log('='.repeat(60));

  const abTest = new ABTest(
    'prompt_v2',
    baselineModel,
    candidateModel,
    0.5 // 50/50 split
  );

  // Simulate requests from different users
  const users = ['user_1', 'user_2', 'user_3', 'user_4'];
  const queries = [
    'How do I reset my password?',
    "What's the refund policy?",
    'How do I cancel?',
    'Where is my order?',
  ];

  for (let i = 0; i < users.length; i++) {
    const [output, assignment] = abTest.run(users[i], queries[i]);
    console.log(`User: ${users[i]}`);
    console.log(`  Variant: ${assignment.variant}`);
    console.log(`  Cohort: ${assignment.cohort}`);
    console.log(`  Output: ${output.substring(0, 50)}...`);
    console.log();
  }

  // Shadow Test Example
  console.log('='.repeat(60));
  console.log('Shadow Test Example');
  console.log('='.repeat(60));

  const shadowTest = new ShadowTest(
    'new_model_test',
    baselineModel,
    candidateModel,
    shadowLogger
  );

  // All users see baseline, candidate runs in background
  for (let i = 0; i < 2; i++) {
    const [baselineOutput, comparison] = shadowTest.run(users[i], queries[i]);
    console.log(`User ${users[i]} sees: ${baselineOutput.substring(0, 50)}...`);
    console.log('(Candidate also ran in background for comparison)');
    console.log();
  }
}

main();

