import { Engine, InMemoryHistoryStore } from '../src/engine';
import { ActivityRegistry } from '../src/activities';
import { DurableWorkflow } from '../src/workflow';

describe('Durable execution: crash after payment succeeds', () => {
  it('resumes from inventory after simulated worker crash, charging exactly once', async () => {
    const registry = new ActivityRegistry();
    const store = new InMemoryHistoryStore();
    const engineA = new Engine(store);

    // Worker A: start the workflow, then simulate crash after inventory fails
    registry.setReserveFailures(1);
    const workflowA = new DurableWorkflow(engineA, registry);

    await expect(workflowA.start('order-123')).rejects.toThrow(
      'Inventory service temporarily unavailable'
    );

    const historyA = engineA.getHistory('order-123');
    expect(historyA.find((e) => e.step === 'chargePayment')?.status).toBe('completed');
    expect(historyA.find((e) => e.step === 'reserveInventory')?.status).toBe('failed');

    // Worker B: new process, same store, resumes from last safe point
    const engineB = new Engine(store);
    const workflowB = new DurableWorkflow(engineB, registry);

    await expect(workflowB.resume('order-123')).resolves.toBeUndefined();

    const historyB = engineB.getHistory('order-123');
    const completed = historyB
      .filter((e) => e.status === 'completed')
      .map((e) => e.step);
    expect(completed).toEqual([
      'chargePayment',
      'reserveInventory',
      'createShipment',
      'sendConfirmation',
    ]);

    // charge was called exactly once
    const chargeKeys = Array.from((registry as any).charges.keys()).filter(
      (k: string) => k.startsWith('charge:')
    );
    expect(chargeKeys).toHaveLength(1);
  });

  it('skips completed steps and retries failed steps on resume', async () => {
    const registry = new ActivityRegistry();
    const store = new InMemoryHistoryStore();

    // Charge succeeds, reserve fails, ship fails
    registry.setReserveFailures(0);
    (registry as any).ship = async () => {
      throw new Error('Shipping provider timeout');
    };

    const engine = new Engine(store);
    const workflow = new DurableWorkflow(engine, registry);

    await expect(workflow.start('order-456')).rejects.toThrow('Shipping provider timeout');

    let history = engine.getHistory('order-456');
    expect(history.filter((e) => e.status === 'completed').map((e) => e.step)).toEqual([
      'chargePayment',
      'reserveInventory',
    ]);
    expect(history.find((e) => e.step === 'createShipment')?.status).toBe('failed');

    // Fix shipping, resume
    delete (registry as any).ship;
    await expect(workflow.resume('order-456')).resolves.toBeUndefined();

    history = engine.getHistory('order-456');
    expect(history.filter((e) => e.status === 'completed').map((e) => e.step)).toEqual([
      'chargePayment',
      'reserveInventory',
      'createShipment',
      'sendConfirmation',
    ]);
  });
});
