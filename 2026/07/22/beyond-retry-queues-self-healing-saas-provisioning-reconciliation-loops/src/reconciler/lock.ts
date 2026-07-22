export class ConcurrencyLock {
  private locks = new Map<string, number>();

  async acquire(tenantId: string, ttlMs: number): Promise<boolean> {
    const now = Date.now();
    const existing = this.locks.get(tenantId);

    if (existing && existing > now) {
      return false;
    }

    this.locks.set(tenantId, now + ttlMs);
    return true;
  }

  release(tenantId: string): void {
    this.locks.delete(tenantId);
  }

  isLocked(tenantId: string): boolean {
    const existing = this.locks.get(tenantId);
    return existing !== undefined && existing > Date.now();
  }
}