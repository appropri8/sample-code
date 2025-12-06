import { Pool } from 'pg';
import { Kafka } from 'kafkajs';
import express from 'express';
import { SagaOrchestrator } from './saga-orchestrator';
import { InventoryService } from './inventory-service';
import { PaymentService } from './payment-service';
import { OrderService } from './order-service';
import { initializeDatabase, seedDatabase } from './database';
import { OrderData } from './types';

const app = express();
app.use(express.json());

// Database connection
const db = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'saga_db',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD || 'postgres'
});

// Kafka connection
const kafka = new Kafka({
  clientId: 'saga-orchestrator',
  brokers: (process.env.KAFKA_BROKERS || 'localhost:9092').split(',')
});

// Initialize services
const orchestrator = new SagaOrchestrator(db, kafka);
const inventoryService = new InventoryService(db, kafka);
const paymentService = new PaymentService(db, kafka);
const orderService = new OrderService(db, kafka);

// API endpoint to start a saga
app.post('/api/orders', async (req, res) => {
  try {
    const orderData: OrderData = req.body;
    
    // Create order record first
    await db.query(`
      INSERT INTO orders (saga_id, customer_id, product_id, quantity, total, status)
      VALUES ($1, $2, $3, $4, $5, 'PENDING')
    `, [orderData.sagaId || 'temp', orderData.customerId, orderData.productId, orderData.quantity, orderData.total]);

    const sagaId = await orchestrator.startSaga('OrderCheckout', orderData);
    
    res.json({
      success: true,
      sagaId,
      message: 'Order saga started'
    });
  } catch (error: any) {
    console.error('Error starting saga:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// API endpoint to get saga state
app.get('/api/sagas/:id', async (req, res) => {
  try {
    const saga = await db.query(
      `SELECT s.*, 
              json_agg(
                json_build_object(
                  'stepName', st.step_name,
                  'sequence', st.step_sequence,
                  'status', st.status,
                  'completedAt', st.completed_at,
                  'error', st.error
                ) ORDER BY st.step_sequence
              ) as steps
       FROM sagas s
       LEFT JOIN saga_steps st ON s.id = st.saga_id
       WHERE s.id = $1
       GROUP BY s.id`,
      [req.params.id]
    );

    if (saga.rows.length === 0) {
      return res.status(404).json({ error: 'Saga not found' });
    }

    res.json(saga.rows[0]);
  } catch (error: any) {
    console.error('Error getting saga:', error);
    res.status(500).json({ error: error.message });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

async function main() {
  try {
    // Initialize database
    await initializeDatabase(db);
    await seedDatabase(db);

    // Connect services
    await orchestrator.connect();
    await inventoryService.connect();
    await paymentService.connect();
    await orderService.connect();

    // Start event loops
    await orchestrator.startEventLoop();
    await inventoryService.start();
    await paymentService.start();
    await orderService.start();

    // Start HTTP server
    const port = process.env.PORT || 3000;
    app.listen(port, () => {
      console.log(`Saga orchestrator server running on port ${port}`);
      console.log(`Health check: http://localhost:${port}/health`);
      console.log(`Start order: POST http://localhost:${port}/api/orders`);
      console.log(`Get saga: GET http://localhost:${port}/api/sagas/:id`);
    });
  } catch (error) {
    console.error('Error starting server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('Shutting down...');
  await orchestrator.disconnect();
  await inventoryService.disconnect();
  await paymentService.disconnect();
  await orderService.disconnect();
  await db.end();
  process.exit(0);
});

if (require.main === module) {
  main();
}

