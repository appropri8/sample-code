import 'dotenv/config';
import { StructuredLLM } from '../src/llm-client';
import { TaskTriageSchema } from '../src/schema';
import { buildStructuredPrompt } from '../src/prompt-builder';
import { getStructuredOutput } from '../src/structured-output';

async function main() {
  // Initialize LLM client
  const llm = new StructuredLLM(
    undefined, // Use OPENAI_API_KEY env var
    'gpt-4',
    30000,
    0.3
  );

  // Example issue descriptions
  const issues = [
    "User reported that they cannot log in after resetting their password. This is blocking them from accessing their account.",
    "Feature request: Add dark mode to the mobile app",
    "Question: How do I export my data?",
    "The payment processing is broken and customers can't complete purchases. This is urgent."
  ];

  console.log('Task Triage Example\n' + '='.repeat(50));

  for (const issue of issues) {
    console.log(`\nIssue: ${issue}`);
    console.log('-'.repeat(50));

    // Build prompt
    const prompt = buildStructuredPrompt(
      TaskTriageSchema,
      issue,
      [
        {
          category: 'bug',
          priority: 3,
          needs_human: true,
          summary: 'User cannot log in after password reset'
        }
      ],
      'Categorize and prioritize the following issue.'
    );

    try {
      // Get structured output
      const result = await getStructuredOutput(
        llm,
        prompt,
        TaskTriageSchema,
        3
      );

      console.log(`Category: ${result.category}`);
      console.log(`Priority: ${result.priority}`);
      console.log(`Needs Human: ${result.needs_human}`);
      if (result.summary) {
        console.log(`Summary: ${result.summary}`);
      }
    } catch (e: any) {
      console.error(`Error: ${e.message}`);
    }
  }
}

main().catch(console.error);

