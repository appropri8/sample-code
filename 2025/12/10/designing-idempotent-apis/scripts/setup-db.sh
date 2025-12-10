#!/bin/bash

# Setup script for PostgreSQL database
# Creates database and runs schema migrations

set -e

DB_NAME="${DB_NAME:-idempotency_db}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "Setting up database: $DB_NAME"

# Create database if it doesn't exist
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "Database already exists"

# Run schema
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
$(cat <<'SCHEMA_EOF'
CREATE TABLE IF NOT EXISTS idempotency_keys (
  idempotency_key VARCHAR(255) PRIMARY KEY,
  status VARCHAR(50) NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
  response_hash VARCHAR(64),
  response_body TEXT,
  user_id VARCHAR(255),
  endpoint VARCHAR(255),
  request_hash VARCHAR(64),
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_endpoint ON idempotency_keys(user_id, endpoint);
CREATE INDEX IF NOT EXISTS idx_expires_at ON idempotency_keys(expires_at);

CREATE TABLE IF NOT EXISTS orders (
  id SERIAL PRIMARY KEY,
  order_id VARCHAR(255) UNIQUE NOT NULL,
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  user_id VARCHAR(255) NOT NULL,
  cart_id VARCHAR(255) NOT NULL,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  total_amount DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_idempotency_key ON orders(idempotency_key);

CREATE TABLE IF NOT EXISTS processed_messages (
  id SERIAL PRIMARY KEY,
  idempotency_key VARCHAR(255) UNIQUE NOT NULL,
  topic VARCHAR(255) NOT NULL,
  partition INTEGER,
  offset BIGINT,
  processed_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_idempotency_key_msg ON processed_messages(idempotency_key);
SCHEMA_EOF
)
EOF

echo "Database setup complete!"
