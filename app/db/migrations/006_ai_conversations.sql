
BEGIN;

-- =========================================================
-- 006: AI CONVERSATIONS, MESSAGES, AND TOOL EXECUTIONS
-- =========================================================

-- 1. Conversations owned by authenticated users
CREATE TABLE IF NOT EXISTS ai_conversations (
    conversation_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    user_id BIGINT NOT NULL
        REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,

    CONSTRAINT chk_ai_conversation_status
        CHECK (
            status IN ('active', 'closed', 'archived')
        )
);


-- 2. Messages belonging to a conversation
CREATE TABLE IF NOT EXISTS ai_messages (
    message_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    conversation_id BIGINT NOT NULL
        REFERENCES ai_conversations(conversation_id)
        ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    model_name VARCHAR(100),
    token_count INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_ai_message_sender
        CHECK (
            sender_type IN (
                'user',
                'assistant',
                'system',
                'tool'
            )
        ),

    CONSTRAINT chk_ai_message_token_count
        CHECK (token_count IS NULL OR token_count >= 0)
);


-- 3. Auditable record of AI tool execution attempts
CREATE TABLE IF NOT EXISTS ai_tool_executions (
    tool_execution_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    conversation_id BIGINT NOT NULL
        REFERENCES ai_conversations(conversation_id),
    message_id BIGINT
        REFERENCES ai_messages(message_id),
    user_id BIGINT
        REFERENCES users(user_id) ON DELETE SET NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_arguments JSONB NOT NULL DEFAULT '{}'::JSONB,
    execution_status VARCHAR(20) NOT NULL DEFAULT 'started',
    result_summary TEXT,
    error_code VARCHAR(100),
    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMPTZ,

    CONSTRAINT chk_ai_tool_execution_status
        CHECK (
            execution_status IN (
                'started',
                'succeeded',
                'failed',
                'denied'
            )
        ),

    CONSTRAINT chk_ai_tool_execution_times
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);


-- 4. Indexes for conversation retrieval and auditing
CREATE INDEX IF NOT EXISTS idx_ai_conversations_user_recent
    ON ai_conversations (user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_messages_conversation_time
    ON ai_messages (conversation_id, created_at);

CREATE INDEX IF NOT EXISTS idx_ai_tool_executions_conversation
    ON ai_tool_executions (conversation_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_tool_executions_user
    ON ai_tool_executions (user_id, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_ai_tool_executions_status
    ON ai_tool_executions (execution_status, started_at DESC);

COMMIT;
