# AI-Powered HRMS Virtual Assistant

An intelligent Human Resource Management System (HRMS) designed to streamline HR operations, automate employee services, and provide AI-powered assistance through natural language interactions.

## Project Overview

The AI-Powered HRMS Virtual Assistant is a web-based HR management solution that aims to simplify employee and HR operations through centralized data management, workflow automation, and AI-powered support.

The system is designed to support employees, HR personnel, managers, and administrators with role-based access to HR services.

An AI-powered virtual assistant will help employees understand company policies, access HR information, and navigate common HR processes using natural language queries.

## Project Objectives

- Centralize employee and HR information.
- Automate routine HR operations and workflows.
- Provide role-based access control.
- Simplify leave application and approval processes.
- Manage employee timesheets and attendance-related records.
- Support employee document requests.
- Provide AI-powered assistance for HR-related queries.
- Enable intelligent company policy search using Retrieval-Augmented Generation (RAG).

## Technology Stack

| Component | Technology |
|---|---|
| Backend Framework | Python, FastAPI |
| Database | PostgreSQL 17 |
| Vector Database | pgvector |
| AI Integration | Google Gemini |
| Embedding Model | gemini-embedding-001 |
| API Documentation | Swagger UI / OpenAPI |
| Authentication | JWT-based authentication (planned) |
| Development Environment | VS Code |
| Version Control | Git and GitHub |

## Core Modules

### 1. Employee Management
- Employee profile management.
- Employee information retrieval.
- Department and job-title management.
- Employee status management.

### 2. Authentication and Authorization
- Secure user authentication.
- Role-based access control.
- Employee, HR, Manager, and Admin roles.
- Permission-based access to HR services.

### 3. Leave Management
- Leave application and tracking.
- Leave balance management.
- Leave approval and rejection workflows.
- Multiple leave categories.
- Configurable leave notice requirements.
- Leave balance deduction after approval.

### 4. HR Document Management
- Employee document requests.
- Employment certificates.
- Salary certificates.
- Experience certificates.
- Relieving certificates.
- HR approval workflows.

### 5. Timesheet Management
- Weekly timesheet management.
- Timesheet entries.
- Timesheet submission.
- Manager approval workflows.

### 6. AI-Powered HR Virtual Assistant
- Natural language interaction.
- HR-related query assistance.
- AI conversation history.
- Tool-based HR operations.
- Context-aware employee assistance.

### 7. RAG-Based HR Policy Knowledge Base
- HR policy document management.
- Policy version management.
- Document chunking and embeddings.
- Semantic search using pgvector.
- Context-aware responses using Google Gemini.

## System Architecture

The system follows a modular backend architecture designed to separate API endpoints, business logic, database operations, and AI services.

```text
                 Employee / HR / Manager / Admin
                              |
                              v
                    FastAPI Application
                              |
               +--------------+--------------+
               |              |              |
               v              v              v
           API Layer     Authentication    AI Assistant
               |              |              |
               v              v              v
          Services       Authorization     RAG Services
               |                             |
               v                             v
          Repositories                  Google Gemini
               |                             |
               v                             v
          PostgreSQL <----------------> pgvector
```

## Project Structure

```text
AI-Powered-HRMS/
│
├── app/
│   ├── ai/
│   ├── api/
│   ├── core/
│   ├── db/
│   │   └── migrations/
│   │       ├── 001_initial_schema.sql
│   │       ├── 002_organization_permissions.sql
│   │       ├── 003_leave_management_rules.sql
│   │       ├── 004_hr_document_management.sql
│   │       ├── 005_timesheets.sql
│   │       ├── 006_ai_conversations.sql
│   │       ├── 007_hr_policy_knowledge_base.sql
│   │       ├── 008_foreign_key_indexes.sql
│   │       └── 009_department_code_not_null.sql
│   │
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   ├── services/
│   └── main.py
│
├── Documents/
│   ├── AI_Powered_HRMS_API_Specification.docx
│   ├── AI_Powered_HRMS_Complete_Database_Data_Dictionary.docx
│   ├── AI_Powered_HRMS_Requirements_Analysis_SRS.pdf
│   └── AI_Powered_HRMS_System_Architecture_Workflow.docx
│
├── docs/
│   ├── AI_Powered_HRMS_Project_Progress_Checklist.md
│   ├── DATABASE_MIGRATION_GUIDE.md
│   ├── HRMS_ENVIRONMENT_VERIFICATION.md
│   ├── POSTGRESQL_COMMAND_REFERENCE.md
│   └── current_schema_snapshot.sql
│
├── images/
│   ├── ERD.png
│   ├── HRMS_Final_ER_Diagram (1).png
│   └── Workflow.jpg
│
├── tests/
│
├── .env.example
├── .gitignore
└── README.md
```

## Database Design

The project uses PostgreSQL 17 as its primary relational database and pgvector for storing and searching policy embeddings.

The database design includes the following areas:

- Employee and organization management.
- User accounts and permissions.
- Leave types, balances, and requests.
- HR document management.
- Timesheets and approvals.
- AI conversations and messages.
- AI tool executions.
- HR policy documents, versions, and chunks.

Nine SQL migration files are currently maintained in the project.

The database schema snapshot and migration instructions are available in the `docs/` directory.

## Installation and Setup

### Prerequisites

Install the following software:

- Python 3.13
- PostgreSQL 17
- pgvector extension
- Visual Studio Code
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/ragina-data/AI-Powered-HRMS.git
```

```bash
cd AI-Powered-HRMS
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate the environment on Windows:

```cmd
.venv\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
```

Additional dependencies will be documented as the application modules are implemented.

### 4. Configure Environment Variables

Create a local `.env` file using `.env.example` as the reference.

Configure your PostgreSQL connection, Google Gemini API key, and application security settings.

**Important:** Never commit `.env`, API keys, database passwords, or other credentials to GitHub.

### 5. Configure PostgreSQL

Create the development database and enable the required PostgreSQL extensions.

```sql
CREATE DATABASE hrms_db;
```

Connect to the database and enable pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Refer to `docs/DATABASE_MIGRATION_GUIDE.md` before applying migrations. Do not run the migrations against an existing database without verifying its current schema and migration status.

### 6. Start the FastAPI Application

From the project root:

```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the FastAPI application is running, access:

| Resource | URL |
|---|---|
| API Home | http://127.0.0.1:8000/ |
| Health Check | http://127.0.0.1:8000/health |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

## Current Development Status

The project is being developed in structured stages.

| Component | Status |
|---|---|
| Project initialization | Completed |
| Python virtual environment | Completed |
| FastAPI initial application | Completed |
| PostgreSQL setup | Completed |
| pgvector installation | Completed |
| Database schema design | Completed |
| SQL migrations 001–009 | Created and validated in test database |
| Database documentation | Created |
| API specification | Documented |
| SRS documentation | Prepared |
| System architecture documentation | Prepared |
| GitHub repository initialization | Completed |
| README documentation | In progress |
| Backend business logic | Pending |
| Authentication implementation | Pending |
| HRMS API implementation | Pending |
| Gemini integration | Pending |
| RAG implementation | Pending |
| Frontend development | Pending |
| Integration and testing | Pending |

## Future Enhancements

- Complete backend API development.
- Implement secure authentication and authorization.
- Develop employee and HR management workflows.
- Integrate Google Gemini with the virtual assistant.
- Implement the RAG-based HR policy assistant.
- Develop a responsive frontend.
- Implement automated testing.
- Add deployment and production configuration.

## Project Documentation

Detailed project documentation is available in the repository:

- **Requirements:** `Documents/AI_Powered_HRMS_Requirements_Analysis_SRS.pdf`
- **API Specification:** `Documents/AI_Powered_HRMS_API_Specification.docx`
- **Database Data Dictionary:** `Documents/AI_Powered_HRMS_Complete_Database_Data_Dictionary.docx`
- **System Architecture:** `Documents/AI_Powered_HRMS_System_Architecture_Workflow.docx`
- **Database Migration Guide:** `docs/DATABASE_MIGRATION_GUIDE.md`
- **Project Progress:** `docs/AI_Powered_HRMS_Project_Progress_Checklist.md`

## Author

**Ragina V**

Data Analyst | Software Developer | AI & Business Intelligence Enthusiast

## Repository

GitHub: https://github.com/ragina-data/AI-Powered-HRMS

---

*This project is an ongoing capstone development project. Features and implementation details will be updated as development progresses.*