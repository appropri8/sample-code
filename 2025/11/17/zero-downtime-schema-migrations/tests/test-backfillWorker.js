const { describe, it, before, after } = require('mocha');
const { expect } = require('chai');
const Database = require('../src/database');
const BackfillWorker = require('../src/backfillWorker');

describe('BackfillWorker', () => {
  let db;
  let worker;
  
  before(async () => {
    db = new Database(process.env.TEST_DATABASE_URL || process.env.DATABASE_URL);
    
    // Setup test data
    await db.query('DELETE FROM orders');
    await db.query('DELETE FROM backfill_progress');
    
    // Insert test orders with old_status but no status
    await db.query(`
      INSERT INTO orders (user_id, amount, old_status, created_at)
      VALUES 
        (1, 100.00, 'pending', NOW()),
        (2, 200.00, 'completed', NOW()),
        (3, 150.00, 'pending', NOW())
    `);
  });
  
  after(async () => {
    await db.close();
  });
  
  it('should backfill orders with status from old_status', async function() {
    this.timeout(10000);
    
    worker = new BackfillWorker(db, {
      batchSize: 10,
      throttleMs: 10,
      resumeTokenKey: 'test_backfill'
    });
    
    const metrics = await worker.run();
    
    expect(metrics.rowsProcessed).to.be.greaterThan(0);
    
    // Verify orders were backfilled
    const result = await db.query('SELECT * FROM orders WHERE status IS NOT NULL');
    expect(result.rows.length).to.be.greaterThan(0);
  });
  
  it('should resume from last processed id', async function() {
    this.timeout(10000);
    
    // Set resume token
    await db.query(`
      INSERT INTO backfill_progress (job_name, last_processed_id)
      VALUES ('test_resume', 1)
      ON CONFLICT (job_name) DO UPDATE SET last_processed_id = 1
    `);
    
    worker = new BackfillWorker(db, {
      batchSize: 1,
      throttleMs: 10,
      resumeTokenKey: 'test_resume'
    });
    
    const lastId = await worker.getResumeToken();
    expect(lastId).to.equal(1);
  });
});

