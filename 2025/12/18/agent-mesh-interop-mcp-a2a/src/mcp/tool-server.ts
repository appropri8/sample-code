/**
 * MCP Tool Server Stub
 * 
 * A simple MCP tool server that exposes tools via the Model Context Protocol.
 * This is a simplified implementation for demonstration purposes.
 */

import { ToolDefinition } from '../types';

export interface MCPRequest {
  method: string;
  params?: {
    name?: string;
    arguments?: unknown;
  };
}

export interface MCPResponse {
  tools?: ToolDefinition[];
  content?: Array<{
    type: string;
    text: string;
  }>;
  error?: string;
}

// Re-export for convenience
export type { ToolDefinition } from '../types';

export class MCPToolServer {
  private tools: Map<string, ToolDefinition> = new Map();

  constructor() {
    this.registerDefaultTools();
  }

  private registerDefaultTools() {
    // Calculator tool
    this.registerTool({
      name: 'calculator',
      description: 'Performs basic arithmetic operations',
      inputSchema: {
        type: 'object',
        properties: {
          operation: {
            type: 'string',
            enum: ['add', 'subtract', 'multiply', 'divide'],
          },
          a: { type: 'number' },
          b: { type: 'number' },
        },
        required: ['operation', 'a', 'b'],
      },
      handler: async (args: any) => {
        const { operation, a, b } = args;
        switch (operation) {
          case 'add':
            return { result: a + b };
          case 'subtract':
            return { result: a - b };
          case 'multiply':
            return { result: a * b };
          case 'divide':
            if (b === 0) {
              return { error: 'Division by zero' };
            }
            return { result: a / b };
          default:
            throw new Error(`Unknown operation: ${operation}`);
        }
      },
    });

    // String reverse tool
    this.registerTool({
      name: 'string_reverse',
      description: 'Reverses a string',
      inputSchema: {
        type: 'object',
        properties: {
          text: { type: 'string' },
        },
        required: ['text'],
      },
      handler: async (args: any) => {
        const { text } = args;
        return { result: text.split('').reverse().join('') };
      },
    });
  }

  registerTool(tool: ToolDefinition): void {
    this.tools.set(tool.name, tool);
  }

  async handleRequest(request: MCPRequest): Promise<MCPResponse> {
    try {
      if (request.method === 'tools/list') {
        return {
          tools: Array.from(this.tools.values()),
        };
      }

      if (request.method === 'tools/call') {
        if (!request.params?.name) {
          return { error: 'Tool name is required' };
        }

        const tool = this.tools.get(request.params.name);
        if (!tool) {
          return { error: `Tool ${request.params.name} not found` };
        }

        const result = await tool.handler(request.params.arguments || {});
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result),
            },
          ],
        };
      }

      return { error: `Unknown method: ${request.method}` };
    } catch (error: any) {
      return {
        error: error.message || 'Unknown error',
      };
    }
  }

  listTools(): ToolDefinition[] {
    return Array.from(this.tools.values());
  }
}

