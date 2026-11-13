
BEGIN;

-- =========================================================
-- 013: AI TOOL EXECUTION CONFIRMATION STATUS
-- =========================================================

ALTER TABLE ai_tool_executions
    DROP CONSTRAINT IF EXISTS chk_ai_tool_execution_status;

ALTER TABLE ai_tool_executions
    ADD CONSTRAINT chk_ai_tool_execution_status
    CHECK (
        execution_status IN (
            'awaiting_confirmation',
            'started',
            'succeeded',
            'failed',
            'denied'
        )
    );

COMMIT;
