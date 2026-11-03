
-- =============================================================================
-- Migration: 001_initial_schema.sql
-- Purpose: Create the original AI-Powered HRMS baseline schema.
-- PostgreSQL Version: 17+
--
-- IMPORTANT:
-- 1. Intended for a NEW, EMPTY database.
-- 2. DO NOT execute against your existing hrms_db.
-- 3. Creates the nine original baseline tables.
-- 4. Later schema changes belong in migrations 002 and above.
-- =============================================================================

BEGIN;

-- =============================================================================
-- 1. EMPLOYEE CODE SEQUENCE
-- =============================================================================

CREATE SEQUENCE public.employee_code_seq
    START WITH 1
    INCREMENT BY 1
    MINVALUE 1
    NO MAXVALUE
    CACHE 1;

-- =============================================================================
-- 2. EMPLOYEES
-- department_id and manager_employee_id are added in migration 002.
-- =============================================================================

CREATE TABLE public.employees (
    employee_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_code VARCHAR(20) NOT NULL
        DEFAULT (
            'EMP' ||
            LPAD(NEXTVAL('public.employee_code_seq')::TEXT, 3, '0')
        ),
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    job_title VARCHAR(100),
    hire_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT employees_employee_code_key UNIQUE (employee_code),
    CONSTRAINT employees_email_key UNIQUE (email)
);

-- =============================================================================
-- 3. ROLES
-- =============================================================================

CREATE TABLE public.roles (
    role_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT roles_role_name_key UNIQUE (role_name)
);

-- =============================================================================
-- 4. USERS
-- =============================================================================

CREATE TABLE public.users (
    user_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id BIGINT,
    email VARCHAR(255) NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_employee_id_key UNIQUE (employee_id),

    CONSTRAINT users_employee_id_fkey
        FOREIGN KEY (employee_id)
        REFERENCES public.employees(employee_id)
);

-- =============================================================================
-- 5. USER ROLES
-- =============================================================================

CREATE TABLE public.user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id),

    CONSTRAINT user_roles_user_id_fkey
        FOREIGN KEY (user_id)
        REFERENCES public.users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT user_roles_role_id_fkey
        FOREIGN KEY (role_id)
        REFERENCES public.roles(role_id)
        ON DELETE CASCADE
);

-- =============================================================================
-- 6. LEAVE BALANCES
-- Leave type catalogue FK is added in migration 003.
-- =============================================================================

CREATE TABLE public.leave_balances (
    leave_balance_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    leave_type VARCHAR(30) NOT NULL,
    entitlement_days NUMERIC(6,2) NOT NULL DEFAULT 0,
    used_days NUMERIC(6,2) NOT NULL DEFAULT 0,
    balance_year INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_entitlement_days
        CHECK (entitlement_days >= 0),

    CONSTRAINT chk_used_days
        CHECK (used_days >= 0 AND used_days <= entitlement_days),

    CONSTRAINT uq_employee_leave_year
        UNIQUE (employee_id, leave_type, balance_year),

    CONSTRAINT leave_balances_employee_id_fkey
        FOREIGN KEY (employee_id)
        REFERENCES public.employees(employee_id)
);

-- =============================================================================
-- 7. LEAVE REQUESTS
-- Leave type catalogue FK is added in migration 003.
-- =============================================================================

CREATE TABLE public.leave_requests (
    leave_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    leave_type VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    days_requested NUMERIC(6,2) NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_days_requested
        CHECK (days_requested > 0),

    CONSTRAINT chk_leave_dates
        CHECK (end_date >= start_date),

    CONSTRAINT chk_leave_request_status
        CHECK (status IN ('pending', 'approved', 'rejected', 'cancelled')),

    CONSTRAINT leave_requests_employee_id_fkey
        FOREIGN KEY (employee_id)
        REFERENCES public.employees(employee_id)
);

-- =============================================================================
-- 8. LEAVE APPROVALS
-- =============================================================================

CREATE TABLE public.leave_approvals (
    leave_approval_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    leave_request_id BIGINT NOT NULL,
    approver_employee_id BIGINT NOT NULL,
    decision VARCHAR(20) NOT NULL,
    comments TEXT,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_leave_approval_decision
        CHECK (decision IN ('approved', 'rejected')),

    CONSTRAINT leave_approvals_leave_request_id_fkey
        FOREIGN KEY (leave_request_id)
        REFERENCES public.leave_requests(leave_request_id),

    CONSTRAINT leave_approvals_approver_employee_id_fkey
        FOREIGN KEY (approver_employee_id)
        REFERENCES public.employees(employee_id)
);

-- =============================================================================
-- 9. HR DOCUMENT REQUESTS
-- Document type catalogue FK is added in migration 004.
-- =============================================================================

CREATE TABLE public.hr_document_requests (
    document_request_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    employee_id BIGINT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    purpose TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_by_employee_id BIGINT,
    processed_at TIMESTAMPTZ,
    remarks TEXT,
    document_reference VARCHAR(255),

    CONSTRAINT chk_document_request_status
        CHECK (
            status IN (
                'pending',
                'processing',
                'completed',
                'rejected',
                'cancelled'
            )
        ),

    CONSTRAINT hr_document_requests_employee_id_fkey
        FOREIGN KEY (employee_id)
        REFERENCES public.employees(employee_id),

    CONSTRAINT hr_document_requests_processed_by_employee_id_fkey
        FOREIGN KEY (processed_by_employee_id)
        REFERENCES public.employees(employee_id)
);

-- =============================================================================
-- 10. AUDIT LOGS
-- =============================================================================

CREATE TABLE public.audit_logs (
    audit_log_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_user_id BIGINT,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(100),
    details JSONB NOT NULL DEFAULT '{}'::JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT audit_logs_actor_user_id_fkey
        FOREIGN KEY (actor_user_id)
        REFERENCES public.users(user_id)
        ON DELETE SET NULL
);

-- =============================================================================
-- 11. BASELINE INDEXES
-- =============================================================================

CREATE INDEX idx_audit_logs_actor
    ON public.audit_logs (actor_user_id);

CREATE INDEX idx_audit_logs_created_at
    ON public.audit_logs (created_at);

CREATE INDEX idx_audit_logs_entity
    ON public.audit_logs (entity_type, entity_id);

CREATE INDEX idx_document_requests_employee_status
    ON public.hr_document_requests (employee_id, status);

CREATE INDEX idx_document_requests_processor
    ON public.hr_document_requests (processed_by_employee_id)
    WHERE processed_by_employee_id IS NOT NULL;

CREATE INDEX idx_document_requests_requested_at
    ON public.hr_document_requests (requested_at DESC);

CREATE INDEX idx_document_requests_type
    ON public.hr_document_requests (document_type);

CREATE INDEX idx_leave_approvals_approver
    ON public.leave_approvals (approver_employee_id);

CREATE INDEX idx_leave_approvals_request
    ON public.leave_approvals (leave_request_id, decided_at DESC);

CREATE INDEX idx_leave_balances_type
    ON public.leave_balances (leave_type);

CREATE INDEX idx_leave_requests_dates
    ON public.leave_requests (start_date, end_date);

CREATE INDEX idx_leave_requests_employee_status
    ON public.leave_requests (employee_id, status);

CREATE INDEX idx_leave_requests_type
    ON public.leave_requests (leave_type);

CREATE INDEX idx_user_roles_role
    ON public.user_roles (role_id);

-- =============================================================================
-- 12. INITIAL ROLE SEED DATA
-- =============================================================================

INSERT INTO public.roles (role_name, description)
VALUES
    (
        'employee',
        'Access to own employee information and requests'
    ),
    (
        'manager',
        'Authorized to review assigned employees requests'
    ),
    (
        'hr',
        'Authorized HR operations and document processing'
    ),
    (
        'admin',
        'Administrative access to manage application settings'
    )
ON CONFLICT (role_name) DO NOTHING;

COMMIT;

-- =============================================================================
-- END OF MIGRATION 001
-- =============================================================================
