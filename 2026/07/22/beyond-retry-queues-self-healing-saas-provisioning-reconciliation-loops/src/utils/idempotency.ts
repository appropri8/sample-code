export function generateIdempotencyKey(
  tenantId: string,
  generation: number,
  actionType: string
): string {
  return `${tenantId}:${generation}:${actionType}`;
}

export async function idempotencyKeyFor(
  key: string,
  _provider?: string,
  _externalResourceId?: string
): Promise<{ tenantId: string; provider: string; externalResourceId: string } | null> {
  // In a real system, this would query the idempotency_keys table
  // For now, return null to indicate no prior execution
  return null;
}

export async function recordIdempotencyKey(
  key: string,
  provider: string,
  externalResourceId: string
): Promise<void> {
  // In a real system, this would insert into idempotency_keys
}