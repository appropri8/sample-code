import { EventStream, TenantEvent } from './event-stream';

export class EventPublisher {
  private cellId: string;
  private globalStream: EventStream;

  constructor(cellId: string, globalStream: EventStream) {
    this.cellId = cellId;
    this.globalStream = globalStream;
  }

  async publishEvent(type: string, tenantId: string, data: any): Promise<void> {
    const event: TenantEvent = {
      type,
      tenantId,
      cellId: this.cellId,
      data,
      timestamp: Date.now()
    };

    await this.globalStream.publish('tenant-events', event);
  }
}


