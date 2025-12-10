import express, { Request, Response } from 'express';
import { Pool } from 'pg';
import { IdempotencyStore, IDEMPOTENCY_SCHEMA } from './database';
import { idempotencyMiddleware, IdempotentRequest } from './idempotency-middleware';
import { OrderService } from './order-service';
import { CreateOrderRequest } from './types';

const app = express();
app.use(express.json());

// Database connection
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'idempotency_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres',
});

// Initialize database schema
async function initializeDatabase() {
  try {
    await pool.query(IDEMPOTENCY_SCHEMA);
    console.log('Database schema initialized');
  } catch (error) {
    console.error('Failed to initialize database:', error);
    process.exit(1);
  }
}

// Initialize services
const idempotencyStore = new IdempotencyStore(pool);
const orderService = new OrderService(pool);

// Apply idempotency middleware to all routes
app.use(idempotencyMiddleware(idempotencyStore));

// Health check
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'ok' });
});

// Create order endpoint
app.post(
  '/api/orders',
  async (req: IdempotentRequest, res: Response) => {
    try {
      const idempotencyKey = req.idempotencyKey;

      if (!idempotencyKey) {
        return res.status(400).json({
          error: 'Idempotency-Key header is required',
          code: 'MISSING_IDEMPOTENCY_KEY'
        });
      }

      const orderRequest: CreateOrderRequest = {
        cart_id: req.body.cart_id,
        items: req.body.items,
        user_id: req.body.user_id || (req as any).user?.id || 'anonymous',
      };

      const order = await orderService.createOrder(
        orderRequest,
        idempotencyKey
      );

      res.status(201).json(order);
    } catch (error: any) {
      console.error('Error creating order:', error);
      res.status(500).json({
        error: 'Failed to create order',
        message: error.message
      });
    }
  }
);

// Get order endpoint
app.get('/api/orders/:orderId', async (req: Request, res: Response) => {
  try {
    const order = await orderService.getOrder(req.params.orderId);

    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }

    res.json(order);
  } catch (error: any) {
    console.error('Error getting order:', error);
    res.status(500).json({
      error: 'Failed to get order',
      message: error.message
    });
  }
});

// Cleanup expired keys endpoint (for cron job)
app.post('/api/admin/cleanup', async (req: Request, res: Response) => {
  try {
    const deleted = await idempotencyStore.cleanupExpired();
    res.json({ deleted });
  } catch (error: any) {
    console.error('Error cleaning up:', error);
    res.status(500).json({
      error: 'Failed to cleanup',
      message: error.message
    });
  }
});

const PORT = process.env.PORT || 3000;

async function start() {
  await initializeDatabase();
  
  app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Health check: http://localhost:${PORT}/health`);
  });
}

start().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
