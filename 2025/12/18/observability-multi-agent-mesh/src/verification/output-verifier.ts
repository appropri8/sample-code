/**
 * Output verifier that checks outputs against JSON schemas and required citations.
 * Validates structure, required fields, and citation requirements.
 */

import Ajv, { JSONSchemaType } from 'ajv';

export interface VerificationResult {
  valid: boolean;
  errors: string[];
  missing_citations: string[];
  schema_errors: string[];
}

export interface VerifierConfig {
  schema?: JSONSchemaType<unknown>;
  required_fields?: string[];
  require_citations?: boolean;
  max_length?: number;
  min_length?: number;
}

export interface Citation {
  tool_name: string;
  data_excerpt: string;
}

/**
 * OutputVerifier checks agent outputs against schemas, required fields, and citations.
 * Returns detailed error messages for debugging.
 */
export class OutputVerifier {
  private ajv: Ajv;

  constructor() {
    this.ajv = new Ajv({ allErrors: true, strict: false });
  }

  verify(
    output: unknown,
    config: VerifierConfig,
    citations?: Citation[]
  ): VerificationResult {
    const errors: string[] = [];
    const missing_citations: string[] = [];
    const schema_errors: string[] = [];

    // Convert output to string for length checks
    const outputStr = typeof output === 'string' ? output : JSON.stringify(output);

    // Check length
    if (config.max_length && outputStr.length > config.max_length) {
      errors.push(`Output exceeds maximum length: ${outputStr.length} > ${config.max_length}`);
    }

    if (config.min_length && outputStr.length < config.min_length) {
      errors.push(`Output below minimum length: ${outputStr.length} < ${config.min_length}`);
    }

    // Check required fields (if output is an object)
    if (config.required_fields && typeof output === 'object' && output !== null) {
      const obj = output as Record<string, unknown>;
      for (const field of config.required_fields) {
        if (!(field in obj) || obj[field] === undefined || obj[field] === null) {
          errors.push(`Missing required field: ${field}`);
        }
      }
    }

    // Check schema
    if (config.schema) {
      const validate = this.ajv.compile(config.schema);
      const valid = validate(output);
      if (!valid) {
        schema_errors.push(...(validate.errors || []).map(err => 
          `${err.instancePath}: ${err.message}`
        ));
        errors.push('Schema validation failed');
      }
    }

    // Check citations
    if (config.require_citations) {
      if (!citations || citations.length === 0) {
        missing_citations.push('No citations provided');
        errors.push('Citations are required but none were provided');
      } else {
        // Check that citations are actually used in output
        const outputLower = outputStr.toLowerCase();
        for (const citation of citations) {
          // Simple check: see if citation data appears in output
          const excerptLower = citation.data_excerpt.toLowerCase().substring(0, 50);
          if (!outputLower.includes(excerptLower)) {
            missing_citations.push(`Citation from ${citation.tool_name} not found in output`);
          }
        }
      }
    }

    return {
      valid: errors.length === 0,
      errors,
      missing_citations,
      schema_errors,
    };
  }
}
