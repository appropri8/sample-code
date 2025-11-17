-- Cleanup function for expired idempotency keys
CREATE OR REPLACE FUNCTION cleanup_expired_idempotency_keys()
RETURNS void AS $$
BEGIN
  DELETE FROM idempotency_keys 
  WHERE expires_at < NOW() - INTERVAL '1 day';
END;
$$ LANGUAGE plpgsql;

-- You can schedule this with pg_cron or a cron job:
-- SELECT cron.schedule('cleanup-idempotency-keys', '0 2 * * *', 'SELECT cleanup_expired_idempotency_keys()');

COMMENT ON FUNCTION cleanup_expired_idempotency_keys IS 'Removes expired idempotency keys older than 1 day past expiration';

