# AI-Powered HRMS — Environment Verification Guide

## 1. Purpose

This document explains how to verify that the AI-Powered HRMS development environment is working correctly.

The verification covers:

- PostgreSQL database service
- PostgreSQL database connection
- FastAPI application
- Uvicorn server
- Health-check endpoint
- Swagger API documentation
- OpenAPI JSON schema

## 2. Project Environment

**Project:** AI-Powered HRMS
**Backend:** FastAPI
**ASGI Server:** Uvicorn
**Database:** PostgreSQL 17
**Database Name:** `hrms_db`
**Local API Address:** `http://127.0.0.1:8000`

## 3. Verify PostgreSQL Service

Open Windows CMD and execute:

```cmd
sc query postgresql-x64-17
```

Expected result:

```text
STATE : 4 RUNNING
```

If the service is not running, start it using:

```cmd
net start postgresql-x64-17
```

## 4. Verify PostgreSQL Database Connection

Connect to the HRMS database:

```cmd
"C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -p 5432 -d hrms_db
```

Execute the following SQL statements.

### 4.1 Check PostgreSQL Version

```sql
SELECT version();
```

### 4.2 Check Database Connection

```sql
SELECT current_database(), current_user;
```

Expected database:

```text
hrms_db
```

### 4.3 Check Application Tables

```sql
SELECT COUNT(*)
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE';
```

Exit PostgreSQL:

```sql
\q
```

## 5. Activate Python Virtual Environment

Navigate to the project directory:

```cmd
cd /d "C:\Data Science\Final Project\AI-Powered-HRMS"
```

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Verify Python:

```cmd
python --version
```

Verify Uvicorn installation:

```cmd
python -m uvicorn --version
```

## 6. Start FastAPI Using Uvicorn

Execute:

```cmd
python -m uvicorn app.main:app --reload
```

Expected output:

```text
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Application startup complete.
```

Keep the CMD window open while testing the API.

To stop the server, press:

```text
Ctrl + C
```

## 7. Verify FastAPI Endpoints

Open a web browser and test the following endpoints.

| Endpoint | URL | Expected result |
|---|---|---|
| Home | http://127.0.0.1:8000/ | Application response |
| Health | http://127.0.0.1:8000/health | Healthy status, if configured |
| Swagger | http://127.0.0.1:8000/docs | Interactive API documentation |
| OpenAPI | http://127.0.0.1:8000/openapi.json | API schema in JSON |

### 7.1 Home Endpoint

Open:

http://127.0.0.1:8000/

Verify that the FastAPI application returns its configured home response.

### 7.2 Health Endpoint

Open:

http://127.0.0.1:8000/health

Verify that the configured health endpoint returns a successful response.

### 7.3 Swagger Documentation

Open:

http://127.0.0.1:8000/docs

Verify that Swagger UI loads and displays the available API endpoints.

### 7.4 OpenAPI Schema

Open:

http://127.0.0.1:8000/openapi.json

Verify that the API specification is returned as JSON.

## 8. Environment Verification Checklist

| Component | Verification | Status |
|---|---|---|
| PostgreSQL service | Service is running | Pending |
| PostgreSQL connection | Connected to `hrms_db` | Pending |
| Python virtual environment | Activated | Pending |
| Uvicorn | Server starts successfully | Pending |
| FastAPI home endpoint | Responds successfully | Pending |
| Health endpoint | Responds successfully | Pending |
| Swagger UI | Loads successfully | Pending |
| OpenAPI schema | Returns JSON | Pending |

Update each status after completing the corresponding verification.

## 9. Troubleshooting

### PostgreSQL connection failure

Check:

- PostgreSQL service status.
- Database name.
- Username and password.
- PostgreSQL port (5432).

### Uvicorn command failure

Check:

- Virtual environment activation.
- Uvicorn installation.
- Correct project directory.
- Application import path (`app.main:app`).

### Swagger page unavailable

Check:

- Whether Uvicorn is running.
- Whether the application started successfully.
- Whether the configured API documentation URL is `/docs`.

### Health endpoint unavailable

Check whether the `/health` route is defined in the FastAPI application.

## 10. Completion Criteria

The environment verification is complete when:

1. PostgreSQL service is running.
2. Connection to `hrms_db` succeeds.
3. Uvicorn starts without errors.
4. FastAPI home endpoint works.
5. Health endpoint works, if configured.
6. Swagger documentation loads.
7. OpenAPI JSON is accessible.

**Important:** This document describes environment verification only. Successful database connectivity does not automatically prove that every application feature or database operation is working.
