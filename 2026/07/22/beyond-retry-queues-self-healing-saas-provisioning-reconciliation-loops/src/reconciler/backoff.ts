export function calculateBackoff(failureCount: number, baseMs: number = 1000, maxMs: number = 60000): number {
  const exponential = baseMs * Math.pow(2, failureCount);
  const withJitter = exponential * (0.5 + Math.random() * 0.5);
  return Math.min(withJitter, maxMs);
}