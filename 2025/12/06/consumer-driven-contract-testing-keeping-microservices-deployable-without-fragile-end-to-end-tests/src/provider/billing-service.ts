import express, { Request, Response } from 'express';
import { PaymentRequest, PaymentResponse, PaymentError } from '../types';

const app = express();
app.use(express.json());

// In-memory store for demo purposes
const payments = new Map<string, PaymentResponse>();

app.post('/payments', async (req: Request, res: Response) => {
  const payment: PaymentRequest = req.body;

  // Validate request
  if (!payment.orderId || !payment.amount || !payment.currency) {
    return res.status(400).json({
      error: 'Invalid request',
      code: 'INVALID_REQUEST',
    } as PaymentError);
  }

  // Simulate payment processing failure for specific card
  if (payment.paymentMethod.last4 === '0000') {
    return res.status(400).json({
      error: 'Payment failed',
      code: 'INSUFFICIENT_FUNDS',
    } as PaymentError);
  }

  // Success response
  const paymentResponse: PaymentResponse = {
    paymentId: `pay_${Math.random().toString(36).substr(2, 9)}`,
    status: 'completed',
    amount: payment.amount,
    currency: payment.currency,
    processedAt: new Date().toISOString(),
  };

  payments.set(paymentResponse.paymentId, paymentResponse);

  res.status(201).json(paymentResponse);
});

app.get('/payments/:paymentId', (req: Request, res: Response) => {
  const payment = payments.get(req.params.paymentId);
  if (!payment) {
    return res.status(404).json({
      error: 'Payment not found',
      code: 'NOT_FOUND',
    } as PaymentError);
  }
  res.json(payment);
});

app.get('/health', (_req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

export default app;

