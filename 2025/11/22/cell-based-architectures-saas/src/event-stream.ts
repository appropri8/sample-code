export interface TenantEvent {
  type: string;
  tenantId: string;
  cellId: string;
  data: any;
  timestamp: number;
}

export interface EventStream {
  publish(topic: string, event: TenantEvent): Promise<void>;
  consume(topic: string): AsyncIterable<TenantEvent>;
}

export class InMemoryEventStream implements EventStream {
  private events: Map<string, TenantEvent[]>;
  private subscribers: Map<string, Array<(event: TenantEvent) => void>>;

  constructor() {
    this.events = new Map();
    this.subscribers = new Map();
  }

  async publish(topic: string, event: TenantEvent): Promise<void> {
    if (!this.events.has(topic)) {
      this.events.set(topic, []);
    }
    this.events.get(topic)!.push(event);

    // Notify subscribers
    const subscribers = this.subscribers.get(topic) || [];
    subscribers.forEach(subscriber => subscriber(event));
  }

  async *consume(topic: string): AsyncIterable<TenantEvent> {
    const events = this.events.get(topic) || [];
    let index = 0;

    while (true) {
      if (index < events.length) {
        yield events[index];
        index++;
      } else {
        // Wait for new events
        await new Promise(resolve => {
          if (!this.subscribers.has(topic)) {
            this.subscribers.set(topic, []);
          }
          this.subscribers.get(topic)!.push((event: TenantEvent) => {
            resolve(event);
          });
        });
        // Get the new event
        const newEvents = this.events.get(topic) || [];
        if (index < newEvents.length) {
          yield newEvents[index];
          index++;
        }
      }
    }
  }

  getEvents(topic: string): TenantEvent[] {
    return this.events.get(topic) || [];
  }

  clear(topic: string): void {
    this.events.delete(topic);
    this.subscribers.delete(topic);
  }
}


