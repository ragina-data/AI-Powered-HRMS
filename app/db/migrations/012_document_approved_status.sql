BEGIN;

-- =====================================================
-- 012: SUPPORT APPROVED STATUS IN HR DOCUMENT MANAGEMENT
-- =====================================================

-- 1. Update document request status constraint

ALTER TABLE hr_document_requests
DROP CONSTRAINT chk_document_request_status;

ALTER TABLE hr_document_requests
ADD CONSTRAINT chk_document_request_status
CHECK (
    status IN (
        'pending',
        'approved',
        'processing',
        'completed',
        'rejected',
        'cancelled'
    )
);


-- 2. Update history new status constraint

ALTER TABLE hr_document_request_history
DROP CONSTRAINT chk_document_history_new_status;

ALTER TABLE hr_document_request_history
ADD CONSTRAINT chk_document_history_new_status
CHECK (
    new_status IN (
        'pending',
        'approved',
        'processing',
        'completed',
        'rejected',
        'cancelled'
    )
);


-- 3. Update history previous status constraint

ALTER TABLE hr_document_request_history
DROP CONSTRAINT chk_document_history_previous_status;

ALTER TABLE hr_document_request_history
ADD CONSTRAINT chk_document_history_previous_status
CHECK (
    previous_status IS NULL
    OR previous_status IN (
        'pending',
        'approved',
        'processing',
        'completed',
        'rejected',
        'cancelled'
    )
);

COMMIT;