import OpenAI from 'openai';

/**
 * Wrapper for LLM API calls with structured output support.
 */
export class StructuredLLM {
  private client: OpenAI;
  private model: string;
  private timeout: number;
  private temperature: number;

  constructor(
    apiKey?: string,
    model: string = 'gpt-4',
    timeout: number = 30000,
    temperature: number = 0.3
  ) {
    const key = apiKey || process.env.OPENAI_API_KEY;
    if (!key) {
      throw new Error('OpenAI API key required (set OPENAI_API_KEY env var)');
    }

    this.client = new OpenAI({ apiKey: key });
    this.model = model;
    this.timeout = timeout;
    this.temperature = temperature;
  }

  async generate(
    prompt: string,
    useJsonMode: boolean = false,
    functions?: Array<{ name: string; description: string; parameters: any }>
  ): Promise<string> {
    try {
      const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
        { role: 'user', content: prompt },
      ];

      const options: OpenAI.Chat.Completions.ChatCompletionCreateParams = {
        model: this.model,
        messages,
        temperature: this.temperature,
      };

      // Use JSON mode if requested and supported
      if (useJsonMode) {
        (options as any).response_format = { type: 'json_object' };
      }

      // Use function calling if provided
      if (functions && functions.length > 0) {
        options.tools = functions.map(f => ({
          type: 'function' as const,
          function: {
            name: f.name,
            description: f.description,
            parameters: f.parameters,
          },
        }));

        if (functions.length === 1) {
          // Force function call if only one function
          options.tool_choice = {
            type: 'function',
            function: { name: functions[0].name },
          };
        }
      }

      const response = await this.client.chat.completions.create(options);

      // Handle function calling response
      if (response.choices[0].message.tool_calls && response.choices[0].message.tool_calls.length > 0) {
        return response.choices[0].message.tool_calls[0].function.arguments || '';
      }

      return response.choices[0].message.content || '';
    } catch (error: any) {
      throw new Error(`LLM call failed: ${error.message}`);
    }
  }

  get modelName(): string {
    return this.model;
  }
}

