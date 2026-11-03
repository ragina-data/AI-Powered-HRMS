BEGIN;

-- AI tool execution lookup
CREATE INDEX IF NOT EXISTS idx_ai_tool_executions_message
    ON public.ai_tool_executions (message_id)
    WHERE message_id IS NOT NULL;

-- Department hierarchy
CREATE INDEX IF NOT EXISTS idx_departments_parent
    ON public.departments (parent_department_id)
    WHERE parent_department_id IS NOT NULL;

-- HR document history and types
CREATE INDEX IF NOT EXISTS idx_document_history_actor
    ON public.hr_document_request_history (action_by_user_id)
    WHERE action_by_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_document_requests_type
    ON public.hr_document_requests (document_type);

-- Policy ownership and version review
CREATE INDEX IF NOT EXISTS idx_hr_policies_owner
    ON public.hr_policies (owner_user_id)
    WHERE owner_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_hr_policy_versions_approver
    ON public.hr_policy_versions (approved_by_user_id)
    WHERE approved_by_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_hr_policy_versions_creator
    ON public.hr_policy_versions (created_by_user_id)
    WHERE created_by_user_id IS NOT NULL;

-- Leave approval and lookup
CREATE INDEX IF NOT EXISTS idx_leave_approvals_approver
    ON public.leave_approvals (approver_employee_id);

CREATE INDEX IF NOT EXISTS idx_leave_balances_type
    ON public.leave_balances (leave_type);

CREATE INDEX IF NOT EXISTS idx_leave_requests_type
    ON public.leave_requests (leave_type);

CREATE INDEX IF NOT EXISTS idx_leave_transactions_actor
    ON public.leave_transactions (actor_user_id)
    WHERE actor_user_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_leave_transactions_request
    ON public.leave_transactions (leave_request_id)
    WHERE leave_request_id IS NOT NULL;

-- Permission assignment lookup
CREATE INDEX IF NOT EXISTS idx_role_permissions_permission
    ON public.role_permissions (permission_id);

CREATE INDEX IF NOT EXISTS idx_user_roles_role
    ON public.user_roles (role_id);

-- Timesheet approval lookup
CREATE INDEX IF NOT EXISTS idx_timesheet_approvals_approver
    ON public.timesheet_approvals (approver_employee_id);

COMMIT;