const express = require('express');
const Database = require('./database');
const OrderRepository = require('./orderRepository');

const app = express();
app.use(express.json());

const db = new Database(process.env.DATABASE_URL);
const orderRepo = new OrderRepository(db);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Create order
app.post('/orders', async (req, res) => {
  try {
    const idempotencyKey = req.headers['idempotency-key'];
    const orderData = {
      userId: req.body.userId,
      amount: req.body.amount,
      status: req.body.status,
      oldStatus: req.body.oldStatus
    };
    
    const order = await orderRepo.createOrderWithRetry(orderData);
    res.status(201).json(order);
  } catch (error) {
    console.error('Create order error', error);
    res.status(500).json({ error: error.message });
  }
});

// Get order
app.get('/orders/:id', async (req, res) => {
  try {
    const order = await orderRepo.getOrder(req.params.id);
    if (!order) {
      return res.status(404).json({ error: 'Order not found' });
    }
    res.json(order);
  } catch (error) {
    console.error('Get order error', error);
    res.status(500).json({ error: error.message });
  }
});

// Shadow read endpoint
app.get('/orders/:id/shadow', async (req, res) => {
  try {
    const comparison = await orderRepo.shadowRead(req.params.id);
    res.json(comparison);
  } catch (error) {
    console.error('Shadow read error', error);
    res.status(500).json({ error: error.message });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log('Environment:', {
    READ_FROM_NEW: process.env.READ_FROM_NEW,
    WRITE_TO_NEW: process.env.WRITE_TO_NEW,
    DUAL_WRITE: process.env.DUAL_WRITE
  });
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await db.close();
  process.exit(0);
});

module.exports = app;

