const Database = require('../src/database');
const BackfillWorker = require('../src/backfillWorker');

async function main() {
  const db = new Database(process.env.DATABASE_URL);
  
  const worker = new BackfillWorker(db, {
    batchSize: 1000,
    throttleMs: 100,
    resumeTokenKey: 'backfill_orders_status'
  });
  
  try {
    await worker.run();
  } catch (error) {
    console.error('Backfill failed', error);
    process.exit(1);
  } finally {
    await db.close();
  }
}

if (require.main === module) {
  main();
}

module.exports = main;

