-- Inbox table for message deduplication
CREATE TABLE IF NOT EXISTS inbox (
  message_id VARCHAR(255) PRIMARY KEY,
  topic VARCHAR(255) NOT NULL,
  payload JSONB NOT NULL,
  processed_at TIMESTAMP NOT NULL DEFAULT NOW(),
  processing_duration_ms INT
);

CREATE INDEX IF NOT EXISTS idx_inbox_processed ON inbox (processed_at);
CREATE INDEX IF NOT EXISTS idx_inbox_topic ON inbox (topic, processed_at);

COMMENT ON TABLE inbox IS 'Inbox pattern for message deduplication';
COMMENT ON COLUMN inbox.message_id IS 'Unique message identifier (from Kafka key)';
COMMENT ON COLUMN inbox.topic IS 'Kafka topic the message came from';
COMMENT ON COLUMN inbox.payload IS 'Message payload as JSON';
COMMENT ON COLUMN inbox.processed_at IS 'When the message was processed';
COMMENT ON COLUMN inbox.processing_duration_ms IS 'How long processing took in milliseconds';

