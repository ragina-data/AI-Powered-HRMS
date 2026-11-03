
BEGIN;

-- =========================================================
-- 005: TIMESHEETS AND APPROVALS
-- =========================================================

-- 1. Timesheet header: one record per employee per week.
CREATE TABLE IF NOT EXISTS timesheets (
    timesheet_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id),
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    submitted_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    total_hours NUMERIC(7,2) NOT NULL DEFAULT 0,
    employee_comments TEXT,
    reviewer_comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_timesheet_employee_period
        UNIQUE (employee_id, period_start),

    CONSTRAINT chk_timesheet_period
        CHECK (
            period_end >= period_start
            AND period_end - period_start = 6
        ),

    CONSTRAINT chk_timesheet_status
        CHECK (
            status IN (
                'draft',
                'submitted',
                'approved',
                'rejected'
            )
        ),

    CONSTRAINT chk_timesheet_total_hours
        CHECK (total_hours >= 0)
);


-- 2. Daily timesheet entries.
CREATE TABLE IF NOT EXISTS timesheet_entries (
    timesheet_entry_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    timesheet_id BIGINT NOT NULL
        REFERENCES timesheets(timesheet_id) ON DELETE CASCADE,
    work_date DATE NOT NULL,
    hours_worked NUMERIC(5,2) NOT NULL,
    task_description TEXT,
    project_code VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_timesheet_work_date
        UNIQUE (timesheet_id, work_date),

    CONSTRAINT chk_timesheet_entry_hours
        CHECK (hours_worked >= 0 AND hours_worked <= 24)
);


-- 3. Approval/rejection history.
CREATE TABLE IF NOT EXISTS timesheet_approvals (
    timesheet_approval_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    timesheet_id BIGINT NOT NULL
        REFERENCES timesheets(timesheet_id),
    approver_employee_id BIGINT NOT NULL
        REFERENCES employees(employee_id),
    decision VARCHAR(20) NOT NULL,
    comments TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_timesheet_approval_decision
        CHECK (decision IN ('approved', 'rejected'))
);


-- 4. Supporting indexes.
CREATE INDEX IF NOT EXISTS idx_timesheets_employee_status
    ON timesheets (employee_id, status);

CREATE INDEX IF NOT EXISTS idx_timesheets_period
    ON timesheets (period_start, period_end);

CREATE INDEX IF NOT EXISTS idx_timesheet_entries_work_date
    ON timesheet_entries (work_date);

CREATE INDEX IF NOT EXISTS idx_timesheet_approvals_timesheet
    ON timesheet_approvals (timesheet_id, decided_at DESC);

COMMIT;
