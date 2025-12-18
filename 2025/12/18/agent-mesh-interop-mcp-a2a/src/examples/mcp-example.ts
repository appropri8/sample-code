/**
 * Example 3: MCP Tool Server and Client
 * 
 * Demonstrates how to create an MCP tool server,
 * register tools, and call them from a client.
 */

import { MCPToolServer } from '../mcp/tool-server';
import { MCPToolClient, InMemoryMCPTransport } from '../mcp/tool-client';

async function runMCPExample() {
  // Create tool server
  const server = new MCPToolServer();

  // Register a custom tool
  server.registerTool({
    name: 'greet',
    description: 'Greets a person by name',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string' },
      },
      required: ['name'],
    },
    handler: async (args: any) => {
      return { result: `Hello, ${args.name}!` };
    },
  });

  // Create client with in-memory transport
  const transport = new InMemoryMCPTransport(server);
  const client = new MCPToolClient(transport);

  // List available tools
  console.log('Available tools:');
  const tools = await client.listTools();
  tools.forEach((tool) => {
    console.log(`  - ${tool.name}: ${tool.description}`);
  });

  // Call calculator tool
  console.log('\nCalling calculator tool:');
  const calcResult = await client.callTool('calculator', {
    operation: 'add',
    a: 10,
    b: 5,
  });
  console.log('Result:', calcResult);

  // Call string reverse tool
  console.log('\nCalling string_reverse tool:');
  const reverseResult = await client.callTool('string_reverse', {
    text: 'Hello, World!',
  });
  console.log('Result:', reverseResult);

  // Call custom greet tool
  console.log('\nCalling greet tool:');
  const greetResult = await client.callTool('greet', {
    name: 'Alice',
  });
  console.log('Result:', greetResult);

  // Try calling non-existent tool
  try {
    await client.callTool('nonexistent', {});
  } catch (error: any) {
    console.log('\nError (expected):', error.message);
  }
}

runMCPExample().catch(console.error);

