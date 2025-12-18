/**
 * Example: Output verifier with schema checks and citation requirements
 * 
 * This demonstrates how to verify agent outputs against schemas,
 * required fields, and citation requirements.
 */

import { OutputVerifier } from '../verification/output-verifier';

async function main() {
  console.log('=== Verification Example: Output Verifier ===\n');

  const verifier = new OutputVerifier();

  // Define output schema
  const outputSchema = {
    type: 'object',
    required: ['status', 'data', 'citations'],
    properties: {
      status: { type: 'string', enum: ['success', 'error'] },
      data: { type: 'object' },
      citations: {
        type: 'array',
        items: {
          type: 'object',
          required: ['tool_name', 'source'],
          properties: {
            tool_name: { type: 'string' },
            source: { type: 'string' },
          },
        },
      },
    },
  } as const;

  // Example 1: Valid output with citations
  console.log('1. Valid output with citations:');
  const validOutput = {
    status: 'success',
    data: { result: 'example', users: 'users table' },
    citations: [
      { tool_name: 'database', source: 'users table' },
    ],
  };

  const result1 = verifier.verify(
    validOutput,
    {
      schema: outputSchema,
      required_fields: ['status', 'data'],
      require_citations: true,
    },
    [
      { tool_name: 'database', data_excerpt: 'users table' },
    ]
  );

  console.log('Valid:', result1.valid);
  console.log('Errors:', result1.errors);
  console.log('✅ Verification passed\n');

  // Example 2: Missing required field
  console.log('2. Missing required field:');
  const missingFieldOutput = {
    status: 'success',
    // data field missing
    citations: [],
  };

  const result2 = verifier.verify(
    missingFieldOutput,
    {
      schema: outputSchema,
      required_fields: ['status', 'data'],
      require_citations: false,
    }
  );

  console.log('Valid:', result2.valid);
  console.log('Errors:', result2.errors);
  console.log('✅ Verification caught missing field\n');

  // Example 3: Schema validation failure
  console.log('3. Schema validation failure:');
  const invalidSchemaOutput = {
    status: 'invalid_status', // not in enum
    data: {},
    citations: [],
  };

  const result3 = verifier.verify(
    invalidSchemaOutput,
    {
      schema: outputSchema,
      require_citations: false,
    }
  );

  console.log('Valid:', result3.valid);
  console.log('Schema errors:', result3.schema_errors);
  console.log('✅ Verification caught schema error\n');

  // Example 4: Missing citations
  console.log('4. Missing citations:');
  const noCitationsOutput = {
    status: 'success',
    data: { result: 'example' },
    citations: [],
  };

  const result4 = verifier.verify(
    noCitationsOutput,
    {
      schema: outputSchema,
      require_citations: true,
    }
  );

  console.log('Valid:', result4.valid);
  console.log('Missing citations:', result4.missing_citations);
  console.log('✅ Verification caught missing citations\n');

  // Example 5: Citation not found in output
  console.log('5. Citation not found in output:');
  const mismatchedCitationOutput = {
    status: 'success',
    data: { result: 'example' },
    citations: [
      { tool_name: 'database', source: 'users table' },
    ],
  };

  const result5 = verifier.verify(
    mismatchedCitationOutput,
    {
      schema: outputSchema,
      require_citations: true,
    },
    [
      { tool_name: 'database', data_excerpt: 'orders table' }, // different from output
    ]
  );

  console.log('Valid:', result5.valid);
  console.log('Missing citations:', result5.missing_citations);
  console.log('✅ Verification caught citation mismatch\n');

  // Example 6: Length validation
  console.log('6. Length validation:');
  const tooLongOutput = 'A'.repeat(5000);
  const result6 = verifier.verify(
    tooLongOutput,
    {
      max_length: 1000,
      min_length: 10,
    }
  );

  console.log('Valid:', result6.valid);
  console.log('Errors:', result6.errors);
  console.log('✅ Verification caught length violation\n');

  console.log('✅ Verification working correctly');
}

main().catch(console.error);
