import { Engine, WorkflowDefinition, ActivityRegistry } from './engine';
import { ChargeIn, ReserveIn, ShipIn, NotifyIn } from './activities';

export class DurableWorkflow {
  constructor(private engine: Engine, private registry: ActivityRegistry) {}

  start(orderId: string): void {
    const def = this.buildDef(orderId);
    this.engine.start(def, { orderId });
  }

  resume(orderId: string): void {
    const def = this.buildDef(orderId);
    this.engine.resume(def, { orderId });
  }

  private buildDef(orderId: string): WorkflowDefinition {
    return {
      name: 'order-fulfillment-v1',
      steps: ['chargePayment', 'reserveInventory', 'createShipment', 'sendConfirmation'],
      run: async (step: string) => {
        switch (step) {
          case 'chargePayment':
            return this.registry.charge({
              orderId,
              idempotencyKey: `payment:charge:${orderId}`,
              amountCents: 4999,
            } as ChargeIn);

          case 'reserveInventory':
            return this.registry.reserve({
              orderId,
              idempotencyKey: `inventory:reserve:${orderId}`,
              sku: 'WIDGET-001',
              quantity: 1,
            } as ReserveIn);

          case 'createShipment':
            return this.registry.ship({
              orderId,
              idempotencyKey: `shipping:create:${orderId}`,
              address: '123 Main St',
            } as ShipIn);

          case 'sendConfirmation':
            return this.registry.notify({
              orderId,
              idempotencyKey: `notification:confirm:${orderId}`,
              email: 'user@example.com',
            } as NotifyIn);

          default:
            throw new Error(`Unknown step: ${step}`);
        }
      },
    };
  }
}
