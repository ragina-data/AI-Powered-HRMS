# AI-Powered HRMS – Database Migration Guide
**Migration directory:** `app/db/migrations/`


## 1. Migration Overview

The project contains eight SQL migration files.

| Migration | File | Description |
|---|---|---|
| 001 | `001_initial_schema.sql` | Baseline HRMS tables |
| 002 | `002_organization_permissions.sql` | Departments and permissions |
| 003 | `003_leave_management_rules.sql` | Leave management |
| 004 | `004_hr_document_management.sql` | HR document management |
| 005 | `005_timesheets.sql` | Timesheet management |
| 006 | `006_ai_conversations.sql` | AI conversations and tool executions |
| 007 | `007_hr_policy_knowledge_base.sql` | HR policy RAG and vector embeddings |
| 008 | `008_foreign_key_indexes.sql` | Foreign-key performance indexes |

## 2. Important Safety Instructions

- Execute migrations only against `hrms_migration_test` during testing.
- Never execute the baseline migration against the existing `hrms_db`.
- Execute migrations in numerical order.
- Stop immediately if any migration fails.
- Do not manually skip failed migrations.
- Verify each migration before proceeding to the next one.
- Keep a backup of important databases.

## 3. Open the Project Directory

Open CMD or the VS Code terminal.

```cmd
cd /d "C:\Data Science\Final Project\AI-Powered-HRMS"
```

## 4. Migration Execution Commands

All commands below explicitly target `hrms_migration_test`.

### Migration 001 – Initial Schema

**Purpose:**

Creates the original baseline HRMS tables:

1. employees
2. roles
3. users
4. user_roles
5. leave_balances
6. leave_requests
7. leave_approvals
8. hr_document_requests
9. audit_logs

Also creates the employee code sequence, indexes, constraints, and initial role records.

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\001_initial_schema.sql"
```

**Verification:**

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

SELECT role_id, role_name, description
FROM roles
ORDER BY role_id;
```

**Expected:**
- 9 baseline tables.
- 4 initial roles.

### Migration 002 – Organization and Permissions

**Purpose:**

Creates:
- departments
- permissions
- role_permissions

Adds:
- employees.department_id
- employees.manager_employee_id

Seeds permission definitions and role-permission mappings.

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\002_organization_permissions.sql"
```

**Verification:**

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

SELECT
    r.role_name,
    COUNT(rp.permission_id) AS permission_count
FROM roles r
LEFT JOIN role_permissions rp
    ON r.role_id = rp.role_id
GROUP BY r.role_name
ORDER BY r.role_name;
```

**Expected permission counts:**

| Role | Permissions |
|---|---:|
| Admin | 19 |
| Employee | 8 |
| HR | 17 |
| Manager | 11 |

### Migration 003 – Leave Management Rules

**Purpose:**

Creates:
- leave_types
- leave_entitlement_rules
- public_holidays
- leave_transactions

Adds leave type foreign keys and leave management indexes.

Seeds seven leave types:
- Annual Leave
- Casual Leave
- Sick Leave
- Unpaid Leave
- Maternity Leave
- Paternity Leave
- Compensatory Leave

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\003_leave_management_rules.sql"
```

**Verification:**

```sql
SELECT
    leave_type_code,
    leave_type_name,
    minimum_notice_days,
    is_active
FROM leave_types
ORDER BY leave_type_code;
```

Check casual leave notice:

```sql
SELECT
    leave_type_code,
    leave_type_name,
    minimum_notice_days
FROM leave_types
WHERE leave_type_code = 'casual';
```

**Expected:** Casual Leave requires 2 calendar days' notice.

Check the four new tables:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'leave_types',
      'leave_entitlement_rules',
      'public_holidays',
      'leave_transactions'
  )
ORDER BY table_name;
```

### Migration 004 – HR Document Management

**Purpose:**

Creates:
- hr_document_types
- hr_document_request_history

Adds document type foreign key and document management indexes.

Seeds four document types:
- Employment Certificate
- Salary Certificate
- Experience Certificate
- Relieving Certificate

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\004_hr_document_management.sql"
```

**Verification:**

```sql
SELECT *
FROM hr_document_types
ORDER BY document_type_code;
```

Check document history table:

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'hr_document_types',
      'hr_document_request_history'
  )
ORDER BY table_name;
```

### Migration 005 – Timesheet Management

**Purpose:**

Creates:
- timesheets
- timesheet_entries
- timesheet_approvals

Includes employee references, weekly timesheet periods, work entries, approval decisions, constraints, and indexes.

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\005_timesheets.sql"
```

**Verification:**

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'timesheets',
      'timesheet_entries',
      'timesheet_approvals'
  )
ORDER BY table_name;
```

### Migration 006 – AI Conversations

**Purpose:**

Creates:
- ai_conversations
- ai_messages
- ai_tool_executions

Supports AI conversation history, message storage, tool execution tracking, and associated user references.

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\006_ai_conversations.sql"
```

**Verification:**

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'ai_conversations',
      'ai_messages',
      'ai_tool_executions'
  )
ORDER BY table_name;
```

### Migration 007 – HR Policy Knowledge Base

**Purpose:**

Creates:
- hr_policies
- hr_policy_versions
- hr_policy_chunks

Supports:
- HR policy storage
- Policy version management
- Policy chunking
- Google Gemini embeddings
- Semantic search
- Full-text search
- HNSW vector indexing

**Prerequisite:**

The pgvector extension must be installed on the PostgreSQL server and enabled in the test database.

Execute in Query Tool connected to `hrms_migration_test`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Check extension:

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

**Execution:**

CREATE EXTENSION IF NOT EXISTS vector;


```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\007_hr_policy_knowledge_base.sql"
```

**Verification:**

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN (
      'hr_policies',
      'hr_policy_versions',
      'hr_policy_chunks'
  )
ORDER BY table_name;
```

Check embedding type:

```sql
SELECT
    column_name,
    data_type,
    udt_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'hr_policy_chunks'
  AND column_name = 'embedding';
```

**Expected configuration:**

| Property | Value |
|---|---|
| Provider | Google |
| Model | gemini-embedding-001 |
| Dimensions | 3072 |
| Storage | halfvec(3072) |
| Index | HNSW |
| Distance | Cosine |

### Migration 008 – Foreign Key Indexes

**Purpose:**

Adds indexes to improve foreign-key lookup and join performance across the HRMS database.

**Execution:**

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_migration_test -v ON_ERROR_STOP=1 -f "C:\Data Science\Final Project\AI-Powered-HRMS\app\db\migrations\008_foreign_key_indexes.sql"
```

**Verification:**

```sql
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

---

## 5. Final Database Verification

After successfully executing all eight migrations, run the following queries.

### 5.1 Total Application Tables

```sql
SELECT COUNT(*) AS total_tables
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';
```

Expected: 27 application tables.

The total may be 28 if you also create the separate utility table `vector_test`.

### 5.2 Complete Table List

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;
```

### 5.3 Foreign Key Count

```sql
SELECT COUNT(*) AS total_foreign_keys
FROM information_schema.table_constraints
WHERE constraint_schema = 'public'
  AND constraint_type = 'FOREIGN KEY';
```

### 5.4 Index Count

```sql
SELECT COUNT(*) AS total_indexes
FROM pg_indexes
WHERE schemaname = 'public';
```

### 5.5 Role and Permission Summary

```sql
SELECT
    r.role_name,
    COUNT(rp.permission_id) AS permission_count
FROM roles r
LEFT JOIN role_permissions rp
    ON r.role_id = rp.role_id
GROUP BY r.role_name
ORDER BY r.role_name;
```

### 5.6 Leave Type Summary

```sql
SELECT
    leave_type_code,
    leave_type_name,
    minimum_notice_days
FROM leave_types
ORDER BY leave_type_code;
```

### 5.7 Vector Extension Verification

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

---

## 6. Migration Execution Tracking

For professional database management, migrations should eventually be recorded in a migration history table.

Example structure:

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    migration_name VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    execution_status VARCHAR(20) NOT NULL DEFAULT 'success'
);
```

A proper migration runner should:
1. Check whether a migration has already been executed.
2. Execute pending migrations in numerical order.
3. Record successful execution.
4. Stop when a migration fails.
5. Avoid rerunning completed migrations.

**Note:** The table above is an example design. The eight SQL files currently do not automatically register themselves in this table.

---

## 7. Final Migration Checklist

- [ ] Migration 001 completed.
- [ ] Migration 002 completed.
- [ ] Migration 003 completed.
- [ ] Migration 004 completed.
- [ ] Migration 005 completed.
- [ ] Migration 006 completed.
- [ ] pgvector extension enabled in test database.
- [ ] Migration 007 completed.
- [ ] Migration 008 completed.
- [ ] All expected application tables verified.
- [ ] Foreign keys verified.
- [ ] Indexes verified.
- [ ] Role-permission mappings verified.
- [ ] Leave types verified.
- [ ] Vector embedding configuration verified.
- [ ] Existing `hrms_db` remains unchanged.

---

## 8. Important Final Note

Successful execution of all eight migrations against `hrms_migration_test` will demonstrate that the migration scripts can build the database structure in a clean environment.

It does not by itself validate every HRMS business rule, application workflow, authorization rule, or AI feature. Those require separate application-level testing.

**Never use the migration testing database as a substitute for a backup of your existing database.**