/**
 * HTTP handler using Redis for idempotency
 * 
 * This example shows how to use Redis instead of PostgreSQL
 * for lower latency idempotency checks.
 */

import express, { Request, Response } from 'express';
import { RedisIdempotencyStore } from '../src/redis-store';
import { OrderService } from '../src/order-service';
import { Pool } from 'pg';
import { CreateOrderRequest } from '../src/types';

const app = express();
app.use(express.json());

// Redis store
const redisStore = new RedisIdempotencyStore('redis://localhost:6379', 86400);

// Database for orders
const pool = new Pool({
  host: 'localhost',
  port: 5432,
  database: 'idempotency_db',
  user: 'postgres',
  password: 'postgres',
});

const orderService = new OrderService(pool);

// Connect Redis
redisStore.connect().catch(console.error);

app.post('/api/orders', async (req: Request, res: Response) => {
  const idempotencyKey = req.headers['idempotency-key'] as string;

  if (!idempotencyKey) {
    return res.status(400).json({
      error: 'Idempotency-Key header is required'
    });
  }

  const requestBody = JSON.stringify(req.body);
  const requestHash = require('crypto')
    .createHash('sha256')
    .update(requestBody)
    .digest('hex');

  try {
    // Check and set atomically
    const state = await redisStore.checkAndSet(idempotencyKey, requestHash);

    if (state === 'exists') {
      // Return cached response
      const cached = await redisStore.get(idempotencyKey);
      if (cached) {
        return res.status(cached.statusCode).json(
          JSON.parse(cached.responseBody)
        );
      }
    }

    if (state === 'processing') {
      return res.status(409).json({
        error: 'Request is already being processed'
      });
    }

    // Process order
    const orderRequest: CreateOrderRequest = {
      cart_id: req.body.cart_id,
      items: req.body.items,
      user_id: req.body.user_id,
    };

    const order = await orderService.createOrder(orderRequest, idempotencyKey);

    // Mark as completed
    const responseBody = JSON.stringify(order);
    await redisStore.markCompleted(idempotencyKey, responseBody, 201);

    res.status(201).json(order);
  } catch (error: any) {
    if (error.message.includes('reused with different request')) {
      return res.status(409).json({
        error: error.message
      });
    }

    await redisStore.markFailed(idempotencyKey, error.message, 500);
    res.status(500).json({ error: error.message });
  }
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
