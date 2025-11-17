-- Idempotency keys table
CREATE TABLE IF NOT EXISTS idempotency_keys (
  key VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL DEFAULT 'processing',
  result JSONB,
  error TEXT,
  request_hash VARCHAR(64),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  completed_at TIMESTAMP,
  expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_idempotency_expires ON idempotency_keys (expires_at);
CREATE INDEX IF NOT EXISTS idx_idempotency_status ON idempotency_keys (status, expires_at);

COMMENT ON TABLE idempotency_keys IS 'Stores idempotency keys and their results';
COMMENT ON COLUMN idempotency_keys.key IS 'The idempotency key from the request header';
COMMENT ON COLUMN idempotency_keys.status IS 'processing, completed, or failed';
COMMENT ON COLUMN idempotency_keys.result IS 'Cached result for completed requests';
COMMENT ON COLUMN idempotency_keys.request_hash IS 'SHA256 hash of request body for validation';
COMMENT ON COLUMN idempotency_keys.expires_at IS 'When this key expires and can be reused';

