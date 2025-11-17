-- Phase 3: Contract - Drop old columns after migration is complete
-- WARNING: Only run this after:
-- 1. All reads are switched to new schema
-- 2. Dual-write has been running for several days
-- 3. You're confident the migration is successful
-- 4. You have a backup

-- Drop old_status column (point of no return)
ALTER TABLE orders DROP COLUMN IF EXISTS old_status;

-- After backfill is complete, add NOT NULL constraint
-- This will briefly lock the table, but should be fast if all rows have values
-- ALTER TABLE orders ALTER COLUMN status SET NOT NULL;

