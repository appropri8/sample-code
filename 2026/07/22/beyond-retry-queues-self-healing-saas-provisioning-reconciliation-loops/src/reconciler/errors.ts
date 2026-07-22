export class RetryableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RetryableError';
  }
}

export class TerminalError extends Error {
  constructor(message: string, public readonly userAction: string) {
    super(message);
    this.name = 'TerminalError';
  }
}