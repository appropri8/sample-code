-- Phase 1: Expand - Add nullable status column (no default, no lock)
-- This is safe because it doesn't lock the table
ALTER TABLE orders ADD COLUMN status VARCHAR(50);

-- Create index concurrently (doesn't lock table)
-- Note: CONCURRENTLY can't be used in a transaction
CREATE INDEX CONCURRENTLY idx_orders_status ON orders(status);

-- Add old_status column for backward compatibility during migration
ALTER TABLE orders ADD COLUMN old_status VARCHAR(50);

