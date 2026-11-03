
BEGIN;

-- =========================================================
-- 004: HR DOCUMENT MANAGEMENT
-- Preserve the existing hr_document_requests table.
-- =========================================================

-- 1. Catalogue of supported HR document types
CREATE TABLE IF NOT EXISTS hr_document_types (
    document_type_id BIGINT GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,
    document_type_code VARCHAR(50) NOT NULL UNIQUE,
    document_type_name VARCHAR(120) NOT NULL,
    description TEXT,
    requires_hr_approval BOOLEAN NOT NULL DEFAULT TRUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO hr_document_types (
    document_type_code,
    document_type_name,
    description,
    requires_hr_approval
)
VALUES
    ('employment_certificate',
     'Employment Certificate',
     'Confirms employment details.',
     TRUE),

    ('salary_certificate',
     'Salary Certificate',
     'Confirms salary details for an authorized purpose.',
     TRUE),

    ('experience_certificate',
     'Experience Certificate',
     'Confirms employment experience.',
     TRUE),

    ('relieving_certificate',
     'Relieving Certificate',
     'Confirms relieving details after applicable clearance.',
     TRUE)
ON CONFLICT (document_type_code) DO NOTHING;


-- 2. Request processing history
-- Each status change or processing action can be recorded.
CREATE TABLE IF NOT EXISTS hr_document_request_history (
    history_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    document_request_id BIGINT NOT NULL
        REFERENCES hr_document_requests(document_request_id),
    previous_status VARCHAR(20),
    new_status VARCHAR(20) NOT NULL,
    action_by_user_id BIGINT
        REFERENCES users(user_id) ON DELETE SET NULL,
    comments TEXT,
    action_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_document_history_new_status
        CHECK (
            new_status IN (
                'pending',
                'processing',
                'completed',
                'rejected',
                'cancelled'
            )
        ),

    CONSTRAINT chk_document_history_previous_status
        CHECK (
            previous_status IS NULL
            OR previous_status IN (
                'pending',
                'processing',
                'completed',
                'rejected',
                'cancelled'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_document_history_request
    ON hr_document_request_history (
        document_request_id,
        action_at DESC
    );


-- 3. Supporting indexes for existing requests
CREATE INDEX IF NOT EXISTS idx_document_requests_employee_status
    ON hr_document_requests (employee_id, status);

CREATE INDEX IF NOT EXISTS idx_document_requests_requested_at
    ON hr_document_requests (requested_at DESC);

CREATE INDEX IF NOT EXISTS idx_document_requests_processor
    ON hr_document_requests (processed_by_employee_id)
    WHERE processed_by_employee_id IS NOT NULL;


-- 4. Record the document type catalogue link while retaining
-- the existing document_type text column for compatibility.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM hr_document_requests r
        LEFT JOIN hr_document_types t
            ON t.document_type_code =
               LOWER(TRIM(r.document_type))
        WHERE t.document_type_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Migration stopped: an existing document_type has no matching document type code. Review existing values before adding the foreign key.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_document_requests_type_code'
          AND conrelid = 'hr_document_requests'::regclass
    ) THEN
        ALTER TABLE hr_document_requests
        ADD CONSTRAINT fk_document_requests_type_code
        FOREIGN KEY (document_type)
        REFERENCES hr_document_types(document_type_code)
        NOT VALID;
    END IF;
END $$;

ALTER TABLE hr_document_requests
    VALIDATE CONSTRAINT fk_document_requests_type_code;

COMMIT;
