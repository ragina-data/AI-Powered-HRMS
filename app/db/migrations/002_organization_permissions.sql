
BEGIN;

-- =====================================================
-- 1. Departments
-- =====================================================
CREATE TABLE IF NOT EXISTS departments (
    department_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    department_code VARCHAR(30) UNIQUE,
    parent_department_id BIGINT
        REFERENCES departments(department_id),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. Extend employees without removing existing columns
-- =====================================================
ALTER TABLE employees
    ADD COLUMN IF NOT EXISTS department_id BIGINT,
    ADD COLUMN IF NOT EXISTS manager_employee_id BIGINT;

-- Add department relationship safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_employees_department'
          AND conrelid = 'public.employees'::regclass
    ) THEN
        ALTER TABLE employees
            ADD CONSTRAINT fk_employees_department
            FOREIGN KEY (department_id)
            REFERENCES departments(department_id);
    END IF;
END $$;

-- Add reporting-manager relationship safely
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_employees_manager'
          AND conrelid = 'public.employees'::regclass
    ) THEN
        ALTER TABLE employees
            ADD CONSTRAINT fk_employees_manager
            FOREIGN KEY (manager_employee_id)
            REFERENCES employees(employee_id);
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_employees_department
    ON employees(department_id);

CREATE INDEX IF NOT EXISTS idx_employees_manager
    ON employees(manager_employee_id);

-- Keep the existing department text column for compatibility.
-- Do not drop it or automatically migrate its values yet.

-- =====================================================
-- 3. Granular permissions
-- =====================================================
CREATE TABLE IF NOT EXISTS permissions (
    permission_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    permission_code VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id BIGINT NOT NULL
        REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id BIGINT NOT NULL
        REFERENCES permissions(permission_id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- =====================================================
-- 4. Seed permission definitions
-- =====================================================
INSERT INTO permissions (permission_code, description)
VALUES
    ('employee.read_self', 'Read own employee profile'),
    ('employee.read_team', 'Read authorized team employee profiles'),
    ('employee.manage', 'Create and update employee records'),
    ('leave.read_self', 'Read own leave balances and requests'),
    ('leave.request', 'Submit own leave requests'),
    ('leave.approve_team', 'Approve or reject authorized team leave requests'),
    ('leave.manage_all', 'Manage leave administration'),
    ('document.request', 'Submit own HR document requests'),
    ('document.read_self', 'Track own HR document requests'),
    ('document.process', 'Process authorized HR document requests'),
    ('timesheet.read_self', 'Read own timesheets'),
    ('timesheet.submit', 'Submit own timesheets'),
    ('timesheet.approve_team', 'Approve authorized team timesheets'),
    ('timesheet.manage_all', 'Manage timesheet administration'),
    ('policy.read', 'Search approved HR policies'),
    ('policy.manage', 'Manage HR policy documents'),
    ('user.manage', 'Manage user accounts and role assignments'),
    ('audit.read', 'Read authorized audit records'),
    ('system.configure', 'Manage application settings')
ON CONFLICT (permission_code) DO NOTHING;

-- =====================================================
-- 5. Assign role permissions
-- =====================================================

-- Employee permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'employee'
  AND p.permission_code IN (
      'employee.read_self',
      'leave.read_self',
      'leave.request',
      'document.request',
      'document.read_self',
      'timesheet.read_self',
      'timesheet.submit',
      'policy.read'
  )
ON CONFLICT DO NOTHING;

-- Manager permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'manager'
  AND p.permission_code IN (
      'employee.read_self',
      'employee.read_team',
      'leave.read_self',
      'leave.request',
      'leave.approve_team',
      'document.request',
      'document.read_self',
      'timesheet.read_self',
      'timesheet.submit',
      'timesheet.approve_team',
      'policy.read'
  )
ON CONFLICT DO NOTHING;

-- HR permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'hr'
  AND p.permission_code IN (
      'employee.read_self',
      'employee.read_team',
      'employee.manage',
      'leave.read_self',
      'leave.request',
      'leave.approve_team',
      'leave.manage_all',
      'document.request',
      'document.read_self',
      'document.process',
      'timesheet.read_self',
      'timesheet.submit',
      'timesheet.approve_team',
      'timesheet.manage_all',
      'policy.read',
      'policy.manage',
      'audit.read'
  )
ON CONFLICT DO NOTHING;

-- Administrator permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.role_name = 'admin'
ON CONFLICT DO NOTHING;

COMMIT;
