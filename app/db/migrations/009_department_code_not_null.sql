-- ============================================================
-- Migration 009: Department Code NOT NULL
-- Purpose: Enforce mandatory department codes.
-- Database: AI-Powered HRMS
-- ============================================================

BEGIN;

-- Precondition: No department may have a NULL or blank code.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM public.departments
        WHERE department_code IS NULL
           OR BTRIM(department_code) = ''
    ) THEN
        RAISE EXCEPTION
            'Migration 009 aborted: department_code contains NULL or blank values.';
    END IF;
END
$$;

-- Enforce mandatory department codes.
ALTER TABLE public.departments
ALTER COLUMN department_code SET NOT NULL;

COMMIT;