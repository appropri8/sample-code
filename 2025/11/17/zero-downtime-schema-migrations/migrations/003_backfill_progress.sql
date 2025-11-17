-- Table to track backfill progress
CREATE TABLE IF NOT EXISTS backfill_progress (
    job_name VARCHAR(255) PRIMARY KEY,
    last_processed_id BIGINT,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

