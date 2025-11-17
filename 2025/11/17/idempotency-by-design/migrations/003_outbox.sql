-- Outbox table for transactional outbox pattern
CREATE TABLE IF NOT EXISTS outbox (
  id BIGSERIAL PRIMARY KEY,
  message_id UUID NOT NULL UNIQUE,
  topic VARCHAR(255) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  published_at TIMESTAMP,
  retry_count INT DEFAULT 0,
  last_error TEXT
);

CREATE INDEX IF NOT EXISTS idx_outbox_unpublished ON outbox (created_at) 
WHERE published_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_outbox_topic ON outbox (topic, published_at);

COMMENT ON TABLE outbox IS 'Transactional outbox for reliable message publishing';
COMMENT ON COLUMN outbox.message_id IS 'Unique message identifier';
COMMENT ON COLUMN outbox.topic IS 'Kafka topic to publish to';
COMMENT ON COLUMN outbox.payload IS 'Message payload as JSON';
COMMENT ON COLUMN outbox.published_at IS 'When the message was successfully published';
COMMENT ON COLUMN outbox.retry_count IS 'Number of retry attempts';

