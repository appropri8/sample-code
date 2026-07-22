import { describe, it } from 'node:test';
import assert from 'node:assert';
import { generateIdempotencyKey } from '../../src/utils/idempotency';
import { calculateBackoff } from '../../src/reconciler/backoff';

describe('Idempotency Utilities', () => {
  it('generates deterministic keys', () => {
    const key1 = generateIdempotencyKey('tenant-1', 5, 'create_identity');
    const key2 = generateIdempotencyKey('tenant-1', 5, 'create_identity');
    assert.strictEqual(key1, key2);
    assert.strictEqual(key1, 'tenant-1:5:create_identity');
  });

  it('changes when generation changes', () => {
    const key1 = generateIdempotencyKey('tenant-1', 5, 'create_identity');
    const key2 = generateIdempotencyKey('tenant-1', 6, 'create_identity');
    assert.notStrictEqual(key1, key2);
  });

  it('backoff increases with failure count', () => {
    const d0 = calculateBackoff(0, 1000, 30000);
    const d1 = calculateBackoff(1, 1000, 30000);
    const d2 = calculateBackoff(2, 1000, 30000);
    assert.ok(d1 >= d0);
    assert.ok(d2 >= d1);
    assert.ok(d2 <= 30000);
  });
});