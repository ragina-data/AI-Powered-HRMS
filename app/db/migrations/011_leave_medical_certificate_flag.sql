BEGIN;

-- =========================================================
-- 011: MEDICAL CERTIFICATE SUBMISSION FLAG
-- AI-Powered HRMS
-- =========================================================

-- Record whether an employee submitted a medical
-- certificate when applying for sick leave.

ALTER TABLE leave_requests
ADD COLUMN medical_certificate_submitted BOOLEAN
NOT NULL DEFAULT FALSE;

-- Medical certificate submission applies only to sick leave.

ALTER TABLE leave_requests
ADD CONSTRAINT chk_medical_certificate_sick_leave
CHECK (
    medical_certificate_submitted = FALSE
    OR leave_type = 'sick'
);

COMMIT;