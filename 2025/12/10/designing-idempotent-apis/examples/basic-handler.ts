/**
 * Basic HTTP handler with idempotency key support
 * 
 * This example shows a simple Express handler that uses idempotency
 * to prevent duplicate order creation.
 */

import express, { Request, Response } from 'express';
import { Pool } from 'pg';
import { IdempotencyStore } from '../src/database';
import { OrderService } from '../src/order-service';
import { CreateOrderRequest } from '../src/types';

const app = express();
app.use(express.json());

const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'idempotency_db',
  user: 'postgres',
  password: 'postgres',
});

const idempotencyStore = new IdempotencyStore(pool);
const orderService = new OrderService(pool);

app.post('/api/orders', async (req: Request, res: Response) => {
  const idempotencyKey = req.headers['idempotency-key'] as string;

  if (!idempotencyKey) {
    return res.status(400).json({
      error: 'Idempotency-Key header is required'
    });
  }

  // Check if already processed
  const existing = await idempotencyStore.findByIdempotencyKey(idempotencyKey);
  
  if (existing && existing.status === 'completed') {
    // Return cached response
    return res.json(JSON.parse(existing.response_body || '{}'));
  }

  // Create processing record
  const requestBody = JSON.stringify(req.body);
  const requestHash = require('crypto')
    .createHash('sha256')
    .update(requestBody)
    .digest('hex');

  try {
    await idempotencyStore.createProcessingRecord(
      idempotencyKey,
      req.body.user_id,
      '/api/orders',
      requestHash
    );
  } catch (error: any) {
    if (error.message === 'Idempotency key already exists') {
      return res.status(409).json({
        error: 'Request is already being processed'
      });
    }
    throw error;
  }

  // Process order
  try {
    const orderRequest: CreateOrderRequest = {
      cart_id: req.body.cart_id,
      items: req.body.items,
      user_id: req.body.user_id,
    };

    const order = await orderService.createOrder(orderRequest, idempotencyKey);

    // Store response
    const responseBody = JSON.stringify(order);
    const responseHash = require('crypto')
      .createHash('sha256')
      .update(responseBody)
      .digest('hex');

    await idempotencyStore.updateCompleted(
      idempotencyKey,
      responseBody,
      responseHash
    );

    res.status(201).json(order);
  } catch (error: any) {
    await idempotencyStore.updateFailed(
      idempotencyKey,
      error.message
    );
    res.status(500).json({ error: error.message });
  }
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
