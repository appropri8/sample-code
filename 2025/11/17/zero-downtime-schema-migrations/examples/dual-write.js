const Database = require('../src/database');
const OrderRepository = require('../src/orderRepository');

async function main() {
  const db = new Database(process.env.DATABASE_URL);
  const orderRepo = new OrderRepository(db);
  
  // Enable dual-write
  process.env.DUAL_WRITE = 'true';
  process.env.WRITE_TO_NEW = 'true';
  
  try {
    // Create order with dual-write
    const order = await orderRepo.createOrder({
      userId: 1,
      amount: 100.00,
      status: 'pending',
      oldStatus: 'pending' // For backward compatibility
    });
    
    console.log('Created order:', order);
    
    // Shadow read to compare
    const comparison = await orderRepo.shadowRead(order.id);
    console.log('Shadow read comparison:', comparison);
    
  } catch (error) {
    console.error('Error', error);
  } finally {
    await db.close();
  }
}

if (require.main === module) {
  main();
}

module.exports = main;

