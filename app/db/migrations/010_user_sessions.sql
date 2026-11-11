x
-- ============================================================
-- Migration 010: User Session Management
-- Purpose: Secure refresh-token storage, rotation and revocation.
-- Database: AI-Powered HRMS
-- ============================================================

BEGIN;

-- Precondition: Verify the users table exists.
DO $$
BEGIN
    IF to_regclass('public.users') IS NULL THEN
        RAISE EXCEPTION
            'Migration 010 aborted: users table does not exist.';
    END IF;
END
$$;

-- Create user sessions table.
CREATE TABLE public.user_sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    session_family_id UUID NOT NULL,

    user_id BIGINT NOT NULL,

    refresh_token_hash VARCHAR(64) NOT NULL,

    access_token_jti UUID NOT NULL,

    expires_at TIMESTAMPTZ NOT NULL,

    revoked_at TIMESTAMPTZ,

    last_used_at TIMESTAMPTZ,

    replaced_by_session_id BIGINT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_user_sessions_user
        FOREIGN KEY (user_id)
        REFERENCES public.users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_user_sessions_replaced_by
        FOREIGN KEY (replaced_by_session_id)
        REFERENCES public.user_sessions(session_id)
        ON DELETE SET NULL,

    CONSTRAINT uq_user_sessions_refresh_token
        UNIQUE (refresh_token_hash),

    CONSTRAINT uq_user_sessions_access_jti
        UNIQUE (access_token_jti),

    CONSTRAINT chk_user_sessions_refresh_hash
        CHECK (refresh_token_hash ~ '^[0-9a-f]{64}$'),

    CONSTRAINT chk_user_sessions_expiration
        CHECK (expires_at > created_at),

    CONSTRAINT chk_user_sessions_revocation
        CHECK (revoked_at IS NULL OR revoked_at >= created_at),

    CONSTRAINT chk_user_sessions_replacement
        CHECK (
            replaced_by_session_id IS NULL
            OR replaced_by_session_id <> session_id
        )
);

-- Index for retrieving sessions belonging to a user.
CREATE INDEX idx_user_sessions_user_id
    ON public.user_sessions(user_id);

-- Index for finding active sessions.
CREATE INDEX idx_user_sessions_active
    ON public.user_sessions(user_id, expires_at)
    WHERE revoked_at IS NULL;

-- Index for identifying all token generations in a session family.
CREATE INDEX idx_user_sessions_family_id
    ON public.user_sessions(session_family_id);

COMMIT;
