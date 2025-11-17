const express = require('express');
const { Pool } = require('pg');
const crypto = require('crypto');

const app = express();
app.use(express.json());

const pool = new Pool({
  connectionString: process.env.DATABASE_URL || 'postgresql://localhost/idempotency_example',
});

// Middleware to extract idempotency key
function getIdempotencyKey(req, res, next) {
  const key = req.headers['idempotency-key'];
  
  if (!key) {
    return res.status(400).json({ 
      error: 'Idempotency-Key header required' 
    });
  }
  
  req.idempotencyKey = key;
  next();
}

// Check idempotency and return cached result if exists
async function checkIdempotency(key) {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    const result = await client.query(
      `SELECT result, status, error 
       FROM idempotency_keys 
       WHERE key = $1 AND expires_at > NOW() 
       FOR UPDATE`,
      [key]
    );
    
    await client.query('COMMIT');
    
    if (result.rows.length > 0) {
      const row = result.rows[0];
      
      if (row.status === 'completed') {
        return { 
          cached: true, 
          result: JSON.parse(row.result),
          status: 'completed'
        };
      }
      
      if (row.status === 'processing') {
        return { 
          cached: true, 
          status: 'processing',
          error: 'Request already processing'
        };
      }
      
      if (row.status === 'failed') {
        return { 
          cached: true, 
          status: 'failed',
          error: row.error
        };
      }
    }
    
    return { cached: false };
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}

// Mark request as processing
async function markProcessing(key, requestHash) {
  await pool.query(
    `INSERT INTO idempotency_keys (key, status, request_hash, expires_at) 
     VALUES ($1, 'processing', $2, NOW() + INTERVAL '24 hours')
     ON CONFLICT (key) DO UPDATE SET 
       status = 'processing',
       request_hash = EXCLUDED.request_hash,
       expires_at = EXCLUDED.expires_at
     WHERE idempotency_keys.expires_at < NOW() OR idempotency_keys.status = 'failed'`,
    [key, requestHash]
  );
}

// Store completed result
async function storeResult(key, result) {
  await pool.query(
    `UPDATE idempotency_keys 
     SET status = 'completed', result = $1, completed_at = NOW()
     WHERE key = $2`,
    [JSON.stringify(result), key]
  );
}

// Store error
async function storeError(key, error) {
  await pool.query(
    `UPDATE idempotency_keys 
     SET status = 'failed', error = $1, completed_at = NOW()
     WHERE key = $2`,
    [error.message, key]
  );
}

// Hash request body for validation
function hashRequest(body) {
  const str = JSON.stringify(body);
  return crypto.createHash('sha256').update(str).digest('hex');
}

// Process order (business logic)
async function processOrder(orderData) {
  const client = await pool.connect();
  
  try {
    await client.query('BEGIN');
    
    const orderId = crypto.randomUUID();
    const order = {
      id: orderId,
      userId: orderData.userId,
      amount: orderData.amount,
      status: 'created',
      createdAt: new Date().toISOString()
    };
    
    // Insert order
    await client.query(
      'INSERT INTO orders (id, user_id, amount, status) VALUES ($1, $2, $3, $4)',
      [orderId, orderData.userId, orderData.amount, 'created']
    );
    
    // Write to outbox
    const messageId = crypto.randomUUID();
    await client.query(
      `INSERT INTO outbox (message_id, topic, payload) 
       VALUES ($1, $2, $3)`,
      [
        messageId,
        'order.created',
        JSON.stringify({ orderId, userId: orderData.userId, amount: orderData.amount })
      ]
    );
    
    await client.query('COMMIT');
    
    return order;
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
}

// Create order endpoint
app.post('/orders', getIdempotencyKey, async (req, res) => {
  const { idempotencyKey } = req;
  const requestHash = hashRequest(req.body);
  
  try {
    // Check for existing result
    const cached = await checkIdempotency(idempotencyKey);
    
    if (cached.cached) {
      if (cached.status === 'completed') {
        return res.status(200).json(cached.result);
      }
      
      if (cached.status === 'processing') {
        return res.status(409).json({ 
          error: cached.error || 'Request already processing' 
        });
      }
      
      if (cached.status === 'failed') {
        return res.status(500).json({ 
          error: cached.error || 'Previous request failed' 
        });
      }
    }
    
    // Validate request
    if (!req.body.userId || !req.body.amount) {
      return res.status(400).json({ 
        error: 'userId and amount are required' 
      });
    }
    
    // Mark as processing
    await markProcessing(idempotencyKey, requestHash);
    
    // Process order (outside transaction to avoid long locks)
    let result;
    try {
      result = await processOrder(req.body);
    } catch (err) {
      await storeError(idempotencyKey, err);
      return res.status(500).json({ 
        error: err.message 
      });
    }
    
    // Store result
    await storeResult(idempotencyKey, result);
    
    res.status(201).json(result);
  } catch (err) {
    console.error('Error processing request:', err);
    res.status(500).json({ 
      error: 'Internal server error' 
    });
  }
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

