export interface ChargeIn {
  orderId: string;
  idempotencyKey: string;
  amountCents: number;
}

export interface ReserveIn {
  orderId: string;
  idempotencyKey: string;
  sku: string;
  quantity: number;
}

export interface ShipIn {
  orderId: string;
  idempotencyKey: string;
  address: string;
}

export interface NotifyIn {
  orderId: string;
  idempotencyKey: string;
  email: string;
}

export class ActivityRegistry {
  private charges = new Map<string, { paymentId: string }>();
  private reserves = new Map<string, { reservationId: string }>();
  private shipments = new Map<string, { shipmentId: string }>();
  private notifications = new Map<string, { notificationId: string }>();

  private reserveFailureCount = 0;

  setReserveFailures(n: number) {
    this.reserveFailureCount = n;
  }

  async charge(input: ChargeIn): Promise<{ paymentId: string }> {
    const key = `charge:${input.idempotencyKey}`;
    if (this.charges.has(key)) {
      return this.charges.get(key)!;
    }

    const result = { paymentId: `pay_${input.orderId}` };
    this.charges.set(key, result);
    return result;
  }

  chargeCallCount(input: ChargeIn): number {
    return this.charges.has(`charge:${input.idempotencyKey}`) ? 1 : 0;
  }

  async reserve(input: ReserveIn): Promise<{ reservationId: string }> {
    const key = `reserve:${input.idempotencyKey}`;
    if (this.reserves.has(key)) {
      return this.reserves.get(key)!;
    }

    if (this.reserveFailureCount > 0) {
      this.reserveFailureCount--;
      throw new Error('Inventory service temporarily unavailable');
    }

    const result = { reservationId: `inv_${input.orderId}` };
    this.reserves.set(key, result);
    return result;
  }

  async ship(input: ShipIn): Promise<{ shipmentId: string }> {
    const key = `ship:${input.idempotencyKey}`;
    if (this.shipments.has(key)) {
      return this.shipments.get(key)!;
    }

    const result = { shipmentId: `ship_${input.orderId}` };
    this.shipments.set(key, result);
    return result;
  }

  async notify(input: NotifyIn): Promise<{ notificationId: string }> {
    const key = `notify:${input.idempotencyKey}`;
    if (this.notifications.has(key)) {
      return this.notifications.get(key)!;
    }

    const result = { notificationId: `notif_${input.orderId}` };
    this.notifications.set(key, result);
    return result;
  }

  reset() {
    this.charges.clear();
    this.reserves.clear();
    this.shipments.clear();
    this.notifications.clear();
    this.reserveFailureCount = 0;
  }
}
