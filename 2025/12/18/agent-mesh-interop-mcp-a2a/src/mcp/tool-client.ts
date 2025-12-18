/**
 * MCP Tool Client
 * 
 * A client for calling MCP tool servers.
 * This is a simplified implementation for demonstration purposes.
 */

import { ToolDefinition, MCPRequest, MCPResponse } from './tool-server';

export interface MCPTransport {
  send(request: MCPRequest): Promise<MCPResponse>;
}

export class MCPToolClient {
  constructor(private transport: MCPTransport) {}

  async listTools(): Promise<ToolDefinition[]> {
    const response = await this.transport.send({
      method: 'tools/list',
    });

    if (response.error) {
      throw new Error(`Failed to list tools: ${response.error}`);
    }

    return response.tools || [];
  }

  async callTool(name: string, args: unknown): Promise<unknown> {
    const response = await this.transport.send({
      method: 'tools/call',
      params: {
        name,
        arguments: args,
      },
    });

    if (response.error) {
      throw new Error(`Failed to call tool ${name}: ${response.error}`);
    }

    if (!response.content || response.content.length === 0) {
      throw new Error(`No content in response from tool ${name}`);
    }

    return JSON.parse(response.content[0].text);
  }
}

/**
 * In-memory transport for testing/demo purposes
 */
export class InMemoryMCPTransport implements MCPTransport {
  constructor(private server: any) {}

  async send(request: MCPRequest): Promise<MCPResponse> {
    return await this.server.handleRequest(request);
  }
}

