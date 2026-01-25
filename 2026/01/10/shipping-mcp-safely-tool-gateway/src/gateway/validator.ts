import Ajv from 'ajv';
import type { ValidationResult, PolicyConstraints } from '../types';
import { isPathAllowed, containsPathTraversal } from '../utils/path-validator';

const ajv = new Ajv({ strict: true, allErrors: true });

/**
 * Tool argument schemas
 */
const TOOL_SCHEMAS: Record<string, object> = {
  filesystem_read: {
    type: 'object',
    additionalProperties: false,
    properties: {
      path: {
        type: 'string',
        pattern: '^[a-zA-Z0-9/._-]+$',
        maxLength: 256,
      },
      maxLines: {
        type: 'integer',
        minimum: 1,
        maximum: 1000,
      },
    },
    required: ['path'],
  },
  filesystem_write: {
    type: 'object',
    additionalProperties: false,
    properties: {
      path: {
        type: 'string',
        pattern: '^[a-zA-Z0-9/._-]+$',
        maxLength: 256,
      },
      content: {
        type: 'string',
        maxLength: 10485760, // 10MB
      },
    },
    required: ['path', 'content'],
  },
  git_diff: {
    type: 'object',
    additionalProperties: false,
    properties: {
      repoPath: {
        type: 'string',
        pattern: '^[a-zA-Z0-9/._-]+$',
        maxLength: 256,
      },
      baseRef: {
        type: 'string',
        maxLength: 128,
      },
      headRef: {
        type: 'string',
        maxLength: 128,
      },
    },
    required: ['repoPath'],
  },
};

/**
 * Validates tool arguments against JSON schema and policy constraints
 */
export async function validateToolArguments(
  tool: string,
  args: Record<string, unknown>,
  constraints?: PolicyConstraints
): Promise<ValidationResult> {
  const errors: string[] = [];

  // Get schema for tool
  const schema = TOOL_SCHEMAS[tool];
  if (!schema) {
    return {
      valid: false,
      errors: [`No schema defined for tool: ${tool}`],
    };
  }

  // Validate against JSON schema
  const validate = ajv.compile(schema);
  const valid = validate(args);

  if (!valid && validate.errors) {
    errors.push(
      ...validate.errors.map(
        (e) => `${e.instancePath || 'root'}: ${e.message}`
      )
    );
  }

  // Check required fields from constraints
  if (constraints?.requiredFields) {
    for (const field of constraints.requiredFields) {
      if (!(field in args)) {
        errors.push(`Missing required field: ${field}`);
      }
    }
  }

  // Check max arguments
  if (constraints?.maxArguments) {
    const argCount = Object.keys(args).length;
    if (argCount > constraints.maxArguments) {
      errors.push(
        `Too many arguments: ${argCount} > ${constraints.maxArguments}`
      );
    }
  }

  // Validate paths if path constraints exist
  if (constraints?.pathConstraints && typeof args.path === 'string') {
    // Check for path traversal
    if (containsPathTraversal(args.path)) {
      errors.push('Path contains traversal attempt');
    }

    // Check against allow-lists
    const pathCheck = isPathAllowed(args.path, constraints.pathConstraints);
    if (!pathCheck.allowed) {
      errors.push(`Path validation failed: ${pathCheck.reason}`);
    }
  }

  // Validate commands if command allow-list exists
  if (constraints?.allowedCommands && typeof args.command === 'string') {
    const command = args.command.split(' ')[0]; // Get base command
    if (!constraints.allowedCommands.includes(command)) {
      errors.push(
        `Command not allowed: ${command}. Allowed: ${constraints.allowedCommands.join(', ')}`
      );
    }
  }

  // Check file size if constraint exists
  if (constraints?.maxFileSize && typeof args.content === 'string') {
    const size = Buffer.byteLength(args.content, 'utf8');
    if (size > constraints.maxFileSize) {
      errors.push(
        `File too large: ${size} bytes > ${constraints.maxFileSize} bytes`
      );
    }
  }

  return {
    valid: errors.length === 0,
    errors: errors.length > 0 ? errors : undefined,
  };
}
