## Stage 39 — PostgreSQL Commands Reference Table

Save this table for future use in your AI-Powered HRMS project. It contains the commands used to verify PostgreSQL, connect to the database, troubleshoot authentication, and create the schema snapshot.

### 1. PostgreSQL installation and service commands

| No. | Command                                                   | Purpose                                                        |
| --- | --------------------------------------------------------- | -------------------------------------------------------------- |
| 1   | `psql --version`                                          | Check PostgreSQL command-line version (if PATH is configured). |
| 2   | `"C:\Program Files\PostgreSQL\17\bin\psql.exe" --version` | Check PostgreSQL version using the full executable path.       |
| 3   | `sc query postgresql-x64-17`                              | Check PostgreSQL Windows service status.                       |
| 4   | `dir "C:\Program Files\PostgreSQL\17\bin"`                | List PostgreSQL executable files.                              |

### 2. Database connection commands

| No. | Command                                                                                     | Purpose                                                |
| --- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| 5   | `"C:\Program Files\PostgreSQL\17\bin\psql.exe" -h localhost -p 5432 -U postgres -d hrms_db` | Connect to the HRMS database using CMD.                |
| 6   | `SELECT current_database();`                                                                | Display the currently connected database.              |
| 7   | `SELECT current_user;`                                                                      | Display the current PostgreSQL user.                   |
| 8   | `SELECT version();`                                                                         | Display PostgreSQL version information.                |
| 9   | `SELECT current_database(), current_user, version();`                                       | Verify database, user and PostgreSQL version together. |
| 10  | `\q`                                                                                        | Exit the PostgreSQL command-line interface.            |
| 11  | `\l`                                                                                        | List all databases.                                    |
| 12  | `\dt`                                                                                       | List tables in the current search schema.              |
| 13  | `\dn`                                                                                       | List database schemas.                                 |
| 14  | `\dx`                                                                                       | List installed extensions.                             |

### 3. Password and authentication commands

| No. | Command                                                      | Purpose                                                                                        |
| --- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| 15  | `ALTER USER postgres WITH PASSWORD 'YourNewStrongPassword';` | Change the PostgreSQL user's password through pgAdmin Query Tool or an authorized SQL session. |
| 16  | `psql -h localhost -p 5432 -U postgres -d hrms_db`           | Test database login from CMD when `psql` is available in PATH.                                 |

Security: Never store your actual database password in project documentation, source code, or GitHub.

### 4. Windows project directory commands

| No. | Command                                                               | Purpose                                                             |
| --- | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 17  | `cd /d "C:\Data Science\Final Project\AI-Powered-HRMS"`               | Navigate to the HRMS project directory.                             |
| 18  | `dir`                                                                 | List files and folders in the current directory.                    |
| 19  | `dir docs`                                                            | List documentation files.                                           |
| 20  | `dir /s /b *.sql`                                                     | Find all SQL migration files recursively.                           |
| 21  | `dir /s /b app\db`                                                    | Display the database folder structure.                              |
| 22  | `dir /s /b app`                                                       | Display all files and folders under the application directory.      |
| 23  | `findstr /S /I /N /C:"CREATE TABLE" app\*.py app\db\migrations\*.sql` | Search application and migration files for CREATE TABLE statements. |

### 5. Database backup and schema snapshot commands

| No. | Command                                                                                                                                                                                                                     | Purpose                                                         |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| 24  | `"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" --version`                                                                                                                                                                | Check pg_dump version.                                          |
| 25  | `"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h localhost -p 5432 -U postgres -d hrms_db --schema-only --no-owner --no-privileges -f "C:\Data Science\Final Project\AI-Powered-HRMS\docs\current_schema_snapshot.sql"` | Export database structure without table records.                |
| 26  | `dir docs\current_schema_snapshot.sql`                                                                                                                                                                                      | Verify that the schema snapshot file exists and check its size. |
| 27  | `type docs\current_schema_snapshot.sql`                                                                                                                                                                                     | Display SQL file contents in CMD.                               |
| 28  | `findstr /I /N "CREATE TABLE" docs\current_schema_snapshot.sql`                                                                                                                                                             | Find table creation statements in the snapshot.                 |
| 29  | `findstr /I /N "CREATE INDEX" docs\current_schema_snapshot.sql`                                                                                                                                                             | Find index creation statements.                                 |
| 30  | `findstr /I /N "FOREIGN KEY" docs\current_schema_snapshot.sql`                                                                                                                                                              | Find foreign key definitions.                                   |

### 6. Important PostgreSQL SQL commands for future database work

| No. | SQL command                                                                                                               | Purpose                                        |
| --- | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| 31  | `SELECT * FROM employees;`                                                                                                | View employee records.                         |
| 32  | `SELECT COUNT(*) FROM employees;`                                                                                         | Count employee records.                        |
| 33  | `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;`                     | List public schema tables.                     |
| 34  | `SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'employees' ORDER BY ordinal_position;` | Inspect employee table columns and data types. |
| 35  | `SELECT * FROM pg_extension;`                                                                                             | Inspect installed PostgreSQL extensions.       |
| 36  | `SELECT * FROM pg_indexes WHERE schemaname = 'public';`                                                                   | Inspect indexes in the public schema.          |

### 7. Important files and their purposes

| File                               | Location             | Purpose                                    |
| ---------------------------------- | -------------------- | ------------------------------------------ |
| `current_schema_snapshot.sql`      | `docs/`              | Snapshot of the actual database structure. |
| `002_organization_permissions.sql` | `app/db/migrations/` | Organization and RBAC schema.              |
| `003_leave_management_rules.sql`   | `app/db/migrations/` | Leave management schema and rules.         |
| `004_hr_document_management.sql`   | `app/db/migrations/` | HR document management schema.             |
| `005_timesheets.sql`               | `app/db/migrations/` | Timesheet schema.                          |
| `006_ai_conversations.sql`         | `app/db/migrations/` | AI conversation and tool execution schema. |
| `007_hr_policy_knowledge_base.sql` | `app/db/migrations/` | HR policy RAG and vector storage schema.   |
| `008_foreign_key_indexes.sql`      | `app/db/migrations/` | Additional foreign key indexes.            |

### 8. Quick reference — Most frequently used commands

| Task                     | Command                                            |
| ------------------------ | -------------------------------------------------- |
| Check PostgreSQL version | `psql --version`                                   |
| Connect to HRMS          | `psql -h localhost -p 5432 -U postgres -d hrms_db` |
| List tables              | `\dt`                                              |
| List databases           | `\l`                                               |
| Check current database   | `SELECT current_database();`                       |
| Count employees          | `SELECT COUNT(*) FROM employees;`                  |
| Exit PostgreSQL          | `\q`                                               |
| List SQL files           | `dir /s /b *.sql`                                  |
| Check snapshot           | `dir docs\current_schema_snapshot.sql`             |
| Create schema backup     | Use command No. 25 above.                          |