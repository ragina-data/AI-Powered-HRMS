
BEGIN;

-- =========================================================
-- 003: LEAVE MANAGEMENT RULES AND CONTROLS
-- AI-Powered HRMS
-- =========================================================

-- 1. Configurable leave types
CREATE TABLE IF NOT EXISTS leave_types (
    leave_type_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    leave_type_code VARCHAR(30) NOT NULL UNIQUE,
    leave_type_name VARCHAR(100) NOT NULL,
    description TEXT,
    is_paid BOOLEAN NOT NULL DEFAULT TRUE,
    requires_approval BOOLEAN NOT NULL DEFAULT TRUE,
    min_notice_calendar_days INTEGER NOT NULL DEFAULT 0,
    max_consecutive_days NUMERIC(6,2),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_leave_type_notice
        CHECK (min_notice_calendar_days >= 0),

    CONSTRAINT chk_leave_type_max_days
        CHECK (
            max_consecutive_days IS NULL
            OR max_consecutive_days > 0
        )
);

-- Initial configurable examples.
-- Confirm these types against the company's HR policy.
INSERT INTO leave_types (
    leave_type_code,
    leave_type_name,
    description,
    is_paid,
    requires_approval,
    min_notice_calendar_days
)
VALUES
    ('annual', 'Annual Leave',
     'Annual leave entitlement defined by company policy.',
     TRUE, TRUE, 0),

    ('casual', 'Casual Leave',
     'Casual leave with a configurable notice requirement.',
     TRUE, TRUE, 2),

    ('sick', 'Sick Leave',
     'Sick leave subject to company policy and applicable law.',
     TRUE, TRUE, 0),

    ('unpaid', 'Unpaid Leave',
     'Approved leave without pay.',
     FALSE, TRUE, 0),

    ('maternity', 'Maternity Leave',
     'Maternity leave subject to applicable policy and law.',
     TRUE, TRUE, 0),

    ('paternity', 'Paternity Leave',
     'Paternity or parental leave subject to applicable policy.',
     TRUE, TRUE, 0),

    ('compensatory', 'Compensatory Leave',
     'Leave granted under an approved compensatory arrangement.',
     TRUE, TRUE, 0)
ON CONFLICT (leave_type_code) DO NOTHING;


-- 2. Connect existing leave tables to the leave type catalogue.
-- The old leave_type text columns are preserved.
-- Abort safely if existing values do not match configured codes.

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM leave_balances lb
        LEFT JOIN leave_types lt
            ON lt.leave_type_code = LOWER(TRIM(lb.leave_type))
        WHERE lt.leave_type_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Migration stopped: a leave_balances.leave_type value has no matching leave_types code.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM leave_requests lr
        LEFT JOIN leave_types lt
            ON lt.leave_type_code = LOWER(TRIM(lr.leave_type))
        WHERE lt.leave_type_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Migration stopped: a leave_requests.leave_type value has no matching leave_types code.';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leave_balances_type_code'
          AND conrelid = 'leave_balances'::regclass
    ) THEN
        ALTER TABLE leave_balances
        ADD CONSTRAINT fk_leave_balances_type_code
        FOREIGN KEY (leave_type)
        REFERENCES leave_types (leave_type_code)
        NOT VALID;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_leave_requests_type_code'
          AND conrelid = 'leave_requests'::regclass
    ) THEN
        ALTER TABLE leave_requests
        ADD CONSTRAINT fk_leave_requests_type_code
        FOREIGN KEY (leave_type)
        REFERENCES leave_types (leave_type_code)
        NOT VALID;
    END IF;
END $$;

ALTER TABLE leave_balances
    VALIDATE CONSTRAINT fk_leave_balances_type_code;

ALTER TABLE leave_requests
    VALIDATE CONSTRAINT fk_leave_requests_type_code;


-- 3. Leave entitlement rules.
-- Rules define standard entitlements by leave type and
-- employment category. Actual employee balances remain
-- in leave_balances.

CREATE TABLE IF NOT EXISTS leave_entitlement_rules (
    entitlement_rule_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    leave_type_id BIGINT NOT NULL
        REFERENCES leave_types (leave_type_id),
    employment_category VARCHAR(50) NOT NULL DEFAULT 'all',
    entitlement_days NUMERIC(7,2) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_entitlement_rule_days
        CHECK (entitlement_days >= 0),

    CONSTRAINT chk_entitlement_rule_dates
        CHECK (
            effective_to IS NULL
            OR effective_to >= effective_from
        )
);

CREATE INDEX IF NOT EXISTS idx_entitlement_rules_lookup
    ON leave_entitlement_rules (
        leave_type_id,
        employment_category,
        effective_from
    );


-- 4. Public holidays.
-- Country and region are configurable for the organization.

CREATE TABLE IF NOT EXISTS public_holidays (
    public_holiday_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    holiday_date DATE NOT NULL,
    holiday_name VARCHAR(150) NOT NULL,
    country_code VARCHAR(2) NOT NULL DEFAULT 'AE',
    region VARCHAR(100) NOT NULL DEFAULT 'all',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_public_holiday
        UNIQUE (holiday_date, country_code, region)
);

CREATE INDEX IF NOT EXISTS idx_public_holidays_date
    ON public_holidays (holiday_date)
    WHERE is_active = TRUE;


-- 5. Leave transaction ledger.
-- days_delta convention:
-- Positive = credit/add days
-- Negative = debit/use days
-- The application must update the matching balance and
-- insert the ledger record in the same database transaction.

CREATE TABLE IF NOT EXISTS leave_transactions (
    leave_transaction_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    employee_id BIGINT NOT NULL
        REFERENCES employees (employee_id),
    leave_balance_id BIGINT NOT NULL
        REFERENCES leave_balances (leave_balance_id),
    leave_request_id BIGINT
        REFERENCES leave_requests (leave_request_id),
    transaction_type VARCHAR(20) NOT NULL,
    days_delta NUMERIC(7,2) NOT NULL,
    notes TEXT,
    actor_user_id BIGINT
        REFERENCES users (user_id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_leave_transaction_type
        CHECK (
            transaction_type IN (
                'accrual',
                'usage',
                'adjustment',
                'reversal'
            )
        ),

    CONSTRAINT chk_leave_transaction_nonzero
        CHECK (days_delta <> 0),

    CONSTRAINT chk_leave_transaction_sign
        CHECK (
            transaction_type NOT IN ('accrual', 'usage')
            OR (
                transaction_type = 'accrual'
                AND days_delta > 0
            )
            OR (
                transaction_type = 'usage'
                AND days_delta < 0
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_leave_transactions_employee
    ON leave_transactions (employee_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_leave_transactions_balance
    ON leave_transactions (leave_balance_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_leave_transactions_request
    ON leave_transactions (leave_request_id)
    WHERE leave_request_id IS NOT NULL;


-- 6. Useful leave-request lookup indexes.

CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_status
    ON leave_requests (employee_id, status);

CREATE INDEX IF NOT EXISTS idx_leave_requests_dates
    ON leave_requests (start_date, end_date);

CREATE INDEX IF NOT EXISTS idx_leave_approvals_request
    ON leave_approvals (leave_request_id, decided_at DESC);


COMMIT;
