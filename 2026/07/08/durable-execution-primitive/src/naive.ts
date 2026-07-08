import { ActivityRegistry, ChargeIn, ReserveIn, ShipIn, NotifyIn } from './activities';

export interface OrderRecord {
  orderId: string;
  status: 'CREATED' | 'PAYMENT_DONE' | 'INVENTORY_RESERVED' | 'SHIPPED' | 'EMAIL_SENT' | string;
  paymentId?: string;
  reservationId?: string;
  shipmentId?: string;
  notificationId?: string;
}

export class NaiveOrderService {
  private orders = new Map<string, OrderRecord>();

  constructor(private registry: ActivityRegistry) {}

  createOrder(orderId: string): OrderRecord {
    const record: OrderRecord = { orderId, status: 'CREATED' };
    this.orders.set(orderId, record);
    return record;
  }

  async fulfill(orderId: string) {
    const order = this.orders.get(orderId)!;
    try {
      order.status = 'PAYMENT_STARTED';
      order.paymentId = (await this.registry.charge({
        orderId,
        idempotencyKey: `payment:charge:${orderId}`,
        amountCents: 4999,
      } as ChargeIn)).paymentId;
      order.status = 'PAYMENT_DONE';

      order.reservationId = (await this.registry.reserve({
        orderId,
        idempotencyKey: `inventory:reserve:${orderId}`,
        sku: 'WIDGET-001',
        quantity: 1,
      } as ReserveIn)).reservationId;
      order.status = 'INVENTORY_RESERVED';

      order.shipmentId = (await this.registry.ship({
        orderId,
        idempotencyKey: `shipping:create:${orderId}`,
        address: '123 Main St',
      } as ShipIn)).shipmentId;
      order.status = 'SHIPPED';

      order.notificationId = (await this.registry.notify({
        orderId,
        idempotencyKey: `notification:confirm:${orderId}`,
        email: 'user@example.com',
      } as NotifyIn)).notificationId;
      order.status = 'EMAIL_SENT';
    } catch (err) {
      order.status = `FAILED:${(err as Error).message}`;
      throw err;
    }
  }

  get order() {
    return this.orders;
  }
}
