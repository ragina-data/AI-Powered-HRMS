
BEGIN;

-- =========================================================
-- 014: EXPAND AI TOOL EXECUTION STATUS COLUMN
-- =========================================================

ALTER TABLE ai_tool_executions
    ALTER COLUMN execution_status TYPE VARCHAR(30);

COMMIT;
