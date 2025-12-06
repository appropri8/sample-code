import { Pact } from '@pact-foundation/pact';
import { Matchers } from '@pact-foundation/pact';
import { OrderService } from '../../src/consumer/order-service';
import { PaymentRequest } from '../../src/types';

describe('OrderService -> BillingService', () => {
  const provider = new Pact({
    consumer: 'OrderService',
    provider: 'BillingService',
    port: 1234,
    log: './logs/pact.log',
    dir: './pacts',
    logLevel: 'INFO',
  });

  let orderService: OrderService;

  beforeAll(() => provider.setup());
  afterAll(() => provider.finalize());
  afterEach(() => provider.verify());

  beforeEach(() => {
    orderService = new OrderService('http://localhost:1234');
  });

  describe('create payment', () => {
    it('creates a payment successfully', async () => {
      const paymentRequest: PaymentRequest = {
        orderId: 'order_123',
        amount: 100.00,
        currency: 'USD',
        paymentMethod: {
          type: 'card',
          last4: '4242',
        },
      };

      const expectedResponse = {
        paymentId: Matchers.string('pay_abc123'),
        status: Matchers.string('completed'),
        amount: Matchers.decimal(100.00),
        currency: Matchers.string('USD'),
        processedAt: Matchers.iso8601DateTime('2025-12-06T10:30:00Z'),
      };

      await provider.addInteraction({
        state: 'order exists and is valid',
        uponReceiving: 'a request to create a payment',
        withRequest: {
          method: 'POST',
          path: '/payments',
          headers: {
            'Content-Type': 'application/json',
          },
          body: paymentRequest,
        },
        willRespondWith: {
          status: 201,
          headers: {
            'Content-Type': 'application/json',
          },
          body: expectedResponse,
        },
      });

      const response = await orderService.createPayment(paymentRequest);

      expect(response.paymentId).toBe('pay_abc123');
      expect(response.status).toBe('completed');
      expect(response.amount).toBe(100.00);
      expect(response.currency).toBe('USD');
    });

    it('handles payment failure', async () => {
      const paymentRequest: PaymentRequest = {
        orderId: 'order_456',
        amount: 50.00,
        currency: 'USD',
        paymentMethod: {
          type: 'card',
          last4: '0000',
        },
      };

      await provider.addInteraction({
        state: 'payment processing fails',
        uponReceiving: 'a request to create a payment that fails',
        withRequest: {
          method: 'POST',
          path: '/payments',
          headers: {
            'Content-Type': 'application/json',
          },
          body: paymentRequest,
        },
        willRespondWith: {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
          },
          body: {
            error: Matchers.string('Payment failed'),
            code: Matchers.string('INSUFFICIENT_FUNDS'),
          },
        },
      });

      await expect(orderService.createPayment(paymentRequest)).rejects.toThrow(
        'Payment failed: Payment failed (INSUFFICIENT_FUNDS)'
      );
    });

    it('handles invalid request', async () => {
      const invalidRequest = {
        orderId: 'order_789',
        // Missing amount and currency
      };

      await provider.addInteraction({
        state: 'invalid payment request',
        uponReceiving: 'a request with missing required fields',
        withRequest: {
          method: 'POST',
          path: '/payments',
          headers: {
            'Content-Type': 'application/json',
          },
          body: invalidRequest,
        },
        willRespondWith: {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
          },
          body: {
            error: Matchers.string('Invalid request'),
            code: Matchers.string('INVALID_REQUEST'),
          },
        },
      });

      await expect(
        orderService.createPayment(invalidRequest as PaymentRequest)
      ).rejects.toThrow();
    });
  });
});

