/**
 * LLM-as-judge module.
 * Uses one LLM to evaluate another LLM's outputs.
 */

export type LLMFunction = (prompt: string) => string;

export function llmJudgePairwise(
  llm: LLMFunction,
  inputText: string,
  outputA: string,
  outputB: string,
  criteria: string = 'Which output is better?'
): 'A' | 'B' {
  const prompt = `You are evaluating two LLM outputs for the same input.

Input: ${inputText}

Output A:
${outputA}

Output B:
${outputB}

Criteria: ${criteria}

Which output is better? Respond with only "A" or "B".`;

  const response = llm(prompt).trim().toUpperCase();

  // Extract A or B
  if (response.includes('A') && !response.substring(0, response.indexOf('A') + 1).includes('B')) {
    return 'A';
  } else if (response.includes('B')) {
    return 'B';
  } else {
    // Default to A if unclear
    return 'A';
  }
}

export function llmJudgeScore(
  llm: LLMFunction,
  inputText: string,
  output: string,
  criteria: string,
  scale: string = '1-5'
): number {
  const prompt = `You are evaluating an LLM output.

Input: ${inputText}

Output:
${output}

Criteria: ${criteria}

Score this output on a scale of ${scale}. Respond with only the number.`;

  const response = llm(prompt).trim();

  // Extract number
  try {
    let score = parseInt(response.split(' ')[0]);
    // Clamp to scale
    if (scale === '1-5') {
      score = Math.max(1, Math.min(5, score));
    }
    return score;
  } catch {
    // Default to middle of scale
    return 3;
  }
}

export function llmJudgeLabel(
  llm: LLMFunction,
  inputText: string,
  output: string,
  expectedBehavior: string | null,
  labelCategories: Record<string, string[]>
): Record<string, string> {
  const labels: Record<string, string> = {};

  for (const [category, possibleValues] of Object.entries(labelCategories)) {
    const valuesStr = possibleValues.join(', ');
    let criteria = `Evaluate ${category}`;
    if (expectedBehavior) {
      criteria += `. Expected behavior: ${expectedBehavior}`;
    }

    const prompt = `You are evaluating an LLM output.

Input: ${inputText}

Output:
${output}

Criteria: ${criteria}

Categorize this output as one of: ${valuesStr}

Respond with only the category value.`;

    const response = llm(prompt).trim().toLowerCase();

    // Find matching value
    let matchedValue: string | null = null;
    for (const value of possibleValues) {
      if (response.includes(value.toLowerCase()) || value.toLowerCase().includes(response)) {
        matchedValue = value;
        break;
      }
    }

    // Default to first value if no match
    labels[category] = matchedValue || possibleValues[0];
  }

  return labels;
}

export class LLMJudge {
  constructor(private llm: LLMFunction) {}

  pairwise(
    inputText: string,
    outputA: string,
    outputB: string,
    criteria: string = 'Which output is better?'
  ): 'A' | 'B' {
    return llmJudgePairwise(this.llm, inputText, outputA, outputB, criteria);
  }

  score(
    inputText: string,
    output: string,
    criteria: string,
    scale: string = '1-5'
  ): number {
    return llmJudgeScore(this.llm, inputText, output, criteria, scale);
  }

  label(
    inputText: string,
    output: string,
    expectedBehavior: string | null,
    labelCategories: Record<string, string[]>
  ): Record<string, string> {
    return llmJudgeLabel(
      this.llm,
      inputText,
      output,
      expectedBehavior,
      labelCategories
    );
  }
}

