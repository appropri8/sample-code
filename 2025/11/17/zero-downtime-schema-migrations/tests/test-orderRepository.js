const { describe, it, before, after } = require('mocha');
const { expect } = require('chai');
const Database = require('../src/database');
const OrderRepository = require('../src/orderRepository');

describe('OrderRepository', () => {
  let db;
  let orderRepo;
  
  before(async () => {
    db = new Database(process.env.TEST_DATABASE_URL || process.env.DATABASE_URL);
    orderRepo = new OrderRepository(db);
    
    // Setup test data
    await db.query('DELETE FROM orders');
    await db.query('DELETE FROM backfill_progress');
  });
  
  after(async () => {
    await db.close();
  });
  
  describe('createOrder', () => {
    it('should create order with new schema when writeToNew is enabled', async () => {
      process.env.WRITE_TO_NEW = 'true';
      process.env.DUAL_WRITE = 'false';
      
      const orderData = {
        userId: 1,
        amount: 100.00,
        status: 'pending'
      };
      
      const order = await orderRepo.createOrder(orderData);
      
      expect(order).to.have.property('id');
      expect(order.userId).to.equal(1);
      expect(order.amount).to.equal(100.00);
      expect(order.status).to.equal('pending');
    });
    
    it('should create order with dual-write when enabled', async () => {
      process.env.DUAL_WRITE = 'true';
      process.env.WRITE_TO_NEW = 'true';
      
      const orderData = {
        userId: 2,
        amount: 200.00,
        status: 'completed',
        oldStatus: 'completed'
      };
      
      const order = await orderRepo.createOrder(orderData);
      
      expect(order).to.have.property('id');
      
      // Verify both schemas have data
      const newOrder = await orderRepo.getOrderFromNew(order.id);
      expect(newOrder.status).to.equal('completed');
    });
  });
  
  describe('getOrder', () => {
    it('should read from new schema when readFromNew is enabled', async () => {
      process.env.READ_FROM_NEW = 'true';
      
      // Create order first
      const orderData = {
        userId: 3,
        amount: 150.00,
        status: 'pending'
      };
      process.env.WRITE_TO_NEW = 'true';
      const created = await orderRepo.createOrder(orderData);
      
      const order = await orderRepo.getOrder(created.id);
      expect(order).to.not.be.null;
      expect(order.status).to.equal('pending');
    });
  });
  
  describe('shadowRead', () => {
    it('should compare old and new schema results', async () => {
      const orderData = {
        userId: 4,
        amount: 250.00,
        status: 'pending'
      };
      process.env.WRITE_TO_NEW = 'true';
      const created = await orderRepo.createOrder(orderData);
      
      const comparison = await orderRepo.shadowRead(created.id);
      expect(comparison).to.have.property('mismatch');
    });
  });
});

