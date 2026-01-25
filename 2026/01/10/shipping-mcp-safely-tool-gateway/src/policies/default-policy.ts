import type { Policy } from '../types';

/**
 * Default policy configuration
 * In production, load from YAML/JSON file
 */
export const defaultPolicies: Policy[] = [
  {
    tool: 'filesystem_read',
    allowedRoles: ['developer', 'analyst'],
    constraints: {
      pathConstraints: [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ],
      maxFileSize: 10 * 1024 * 1024, // 10MB
    },
    sandbox: {
      type: 'container',
      networkPolicy: 'deny',
      timeout: 30000,
      memoryLimit: '256m',
      cpuLimit: '1.0',
    },
    constraints: {
      rateLimit: {
        perUser: {
          requests: 100,
          window: 60000, // 1 minute
        },
      },
    },
  },
  {
    tool: 'filesystem_write',
    allowedRoles: ['developer'],
    requiresElevation: true,
    constraints: {
      pathConstraints: [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ],
      maxFileSize: 10 * 1024 * 1024, // 10MB
    },
    sandbox: {
      type: 'container',
      networkPolicy: 'deny',
      timeout: 30000,
      memoryLimit: '512m',
      cpuLimit: '1.0',
    },
    constraints: {
      rateLimit: {
        perUser: {
          requests: 50,
          window: 60000,
        },
      },
    },
  },
  {
    tool: 'git_diff',
    allowedRoles: ['developer'],
    constraints: {
      pathConstraints: [
        {
          type: 'allow',
          pattern: '/workspace/**',
          basePath: '/workspace',
        },
      ],
      allowedCommands: ['git'],
    },
    sandbox: {
      type: 'container',
      networkPolicy: 'deny',
      timeout: 60000,
      memoryLimit: '512m',
      cpuLimit: '1.0',
    },
    constraints: {
      rateLimit: {
        perUser: {
          requests: 100,
          window: 60000,
        },
      },
    },
  },
];
