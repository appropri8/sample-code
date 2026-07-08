export interface WorkflowDefinition {
  name: string;
  steps: string[];
  run: (step: string, ctx: { orderId: string }) => Promise<unknown>;
}

export type HistoryEntry =
  | { step: string; status: 'started'; ts: number }
  | { step: string; status: 'completed'; result: unknown; ts: number }
  | { step: string; status: 'failed'; error: Error; ts: number };

export interface HistoryStore {
  get(id: string): HistoryEntry[];
  append(id: string, entry: HistoryEntry): void;
  clear(id: string): void;
}

export class InMemoryHistoryStore implements HistoryStore {
  private data = new Map<string, HistoryEntry[]>();

  get(id: string): HistoryEntry[] {
    return this.data.get(id) || [];
  }

  append(id: string, entry: HistoryEntry): void {
    const list = this.data.get(id) || [];
    list.push(entry);
    this.data.set(id, list);
  }

  clear(id: string): void {
    this.data.delete(id);
  }
}

export class Engine {
  constructor(private store: HistoryStore = new InMemoryHistoryStore()) {}

  async start(def: WorkflowDefinition, ctx: { orderId: string }): Promise<void> {
    const id = ctx.orderId;
    const entries = this.store.get(id);
    entries.length = 0;

    for (const step of def.steps) {
      this.store.append(id, { step, status: 'started', ts: Date.now() });

      try {
        const result = await def.run(step, ctx);
        this.store.append(id, { step, status: 'completed', result, ts: Date.now() });
      } catch (err) {
        this.store.append(id, { step, status: 'failed', error: err as Error, ts: Date.now() });
        throw err;
      }
    }
  }

  async resume(def: WorkflowDefinition, ctx: { orderId: string }): Promise<void> {
    const id = ctx.orderId;
    const entries = this.store.get(id);
    const completed = new Set(entries.filter((e) => e.status === 'completed').map((e) => e.step));

    for (const step of def.steps) {
      if (completed.has(step)) {
        continue;
      }

      this.store.append(id, { step, status: 'started', ts: Date.now() });

      try {
        const result = await def.run(step, ctx);
        this.store.append(id, { step, status: 'completed', result, ts: Date.now() });
      } catch (err) {
        this.store.append(id, { step, status: 'failed', error: err as Error, ts: Date.now() });
        throw err;
      }
    }
  }

  getHistory(id: string): HistoryEntry[] {
    return this.store.get(id);
  }
}
