-- Feedback table schema
CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    turn_id INTEGER NOT NULL,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    prompt_version VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    feedback_type VARCHAR(50), -- 'explicit', 'implicit', 'outcome'
    feedback_value JSONB, -- Flexible structure for different feedback types
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    user_id_hash VARCHAR(64),
    metadata JSONB -- Additional context
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_feedback_conversation ON feedback(conversation_id, turn_id);
CREATE INDEX IF NOT EXISTS idx_feedback_prompt_version ON feedback(prompt_version);
CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_feedback_request_id ON feedback(request_id);

-- A/B test assignments table
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id SERIAL PRIMARY KEY,
    test_name VARCHAR(255) NOT NULL,
    user_id_hash VARCHAR(64) NOT NULL,
    variant VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(test_name, user_id_hash)
);

CREATE INDEX IF NOT EXISTS idx_ab_test_name ON ab_test_assignments(test_name);
CREATE INDEX IF NOT EXISTS idx_ab_test_user ON ab_test_assignments(user_id_hash);

