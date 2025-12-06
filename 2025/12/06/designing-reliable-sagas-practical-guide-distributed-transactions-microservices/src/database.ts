import { Pool } from 'pg';

export async function initializeDatabase(db: Pool): Promise<void> {
  // Create sagas table
  await db.query(`
    CREATE TABLE IF NOT EXISTS sagas (
      id VARCHAR(255) PRIMARY KEY,
      state VARCHAR(50) NOT NULL,
      type VARCHAR(100) NOT NULL,
      payload JSONB NOT NULL,
      started_at TIMESTAMP NOT NULL,
      completed_at TIMESTAMP,
      compensated_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW(),
      updated_at TIMESTAMP DEFAULT NOW()
    );
  `);

  // Create saga_steps table
  await db.query(`
    CREATE TABLE IF NOT EXISTS saga_steps (
      id SERIAL PRIMARY KEY,
      saga_id VARCHAR(255) NOT NULL,
      step_name VARCHAR(100) NOT NULL,
      step_sequence INTEGER NOT NULL,
      status VARCHAR(50) NOT NULL,
      result JSONB,
      error TEXT,
      completed_at TIMESTAMP,
      failed_at TIMESTAMP,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  // Create products table (for inventory)
  await db.query(`
    CREATE TABLE IF NOT EXISTS products (
      id VARCHAR(255) PRIMARY KEY,
      name VARCHAR(255) NOT NULL,
      stock INTEGER NOT NULL DEFAULT 0
    );
  `);

  // Create reservations table
  await db.query(`
    CREATE TABLE IF NOT EXISTS reservations (
      id SERIAL PRIMARY KEY,
      saga_id VARCHAR(255) NOT NULL,
      product_id VARCHAR(255) NOT NULL,
      quantity INTEGER NOT NULL,
      status VARCHAR(50) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  // Create accounts table (for payments)
  await db.query(`
    CREATE TABLE IF NOT EXISTS accounts (
      id SERIAL PRIMARY KEY,
      customer_id VARCHAR(255) NOT NULL UNIQUE,
      balance DECIMAL(10, 2) NOT NULL DEFAULT 0
    );
  `);

  // Create payments table
  await db.query(`
    CREATE TABLE IF NOT EXISTS payments (
      id SERIAL PRIMARY KEY,
      saga_id VARCHAR(255) NOT NULL,
      customer_id VARCHAR(255) NOT NULL,
      amount DECIMAL(10, 2) NOT NULL,
      status VARCHAR(50) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW()
    );
  `);

  // Create orders table
  await db.query(`
    CREATE TABLE IF NOT EXISTS orders (
      id SERIAL PRIMARY KEY,
      saga_id VARCHAR(255) NOT NULL,
      customer_id VARCHAR(255) NOT NULL,
      product_id VARCHAR(255) NOT NULL,
      quantity INTEGER NOT NULL,
      total DECIMAL(10, 2) NOT NULL,
      status VARCHAR(50) NOT NULL,
      created_at TIMESTAMP DEFAULT NOW(),
      confirmed_at TIMESTAMP,
      cancelled_at TIMESTAMP
    );
  `);

  // Create indexes
  await db.query(`
    CREATE INDEX IF NOT EXISTS idx_sagas_state ON sagas(state);
    CREATE INDEX IF NOT EXISTS idx_saga_steps_saga_id ON saga_steps(saga_id);
  `);

  console.log('Database initialized');
}

export async function seedDatabase(db: Pool): Promise<void> {
  // Seed products
  await db.query(`
    INSERT INTO products (id, name, stock) VALUES
    ('prod-1', 'Product 1', 100),
    ('prod-2', 'Product 2', 50)
    ON CONFLICT (id) DO NOTHING;
  `);

  // Seed accounts
  await db.query(`
    INSERT INTO accounts (customer_id, balance) VALUES
    ('cust-1', 1000.00),
    ('cust-2', 500.00)
    ON CONFLICT (customer_id) DO NOTHING;
  `);

  console.log('Database seeded');
}

