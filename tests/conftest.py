
"""
Shared PostgreSQL Integration Test Fixtures

Development database:
    hrms_db

Integration test database:
    hrms_db

All integration test changes are rolled back.
"""

import pytest

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_db
from app.main import app


TEST_DATABASE_NAME = "hrms_db"


# ============================================================
# 1. ISOLATED TEST DATABASE ENGINE
# ============================================================

@pytest.fixture(scope="session")
def test_engine():

    test_url = make_url(
        settings.DATABASE_URL
    ).set(
        database=TEST_DATABASE_NAME
    )

    engine = create_engine(
        test_url,
        pool_pre_ping=True,
    )

    try:
        with engine.connect() as connection:

            actual_database = connection.execute(
                text("SELECT current_database()")
            ).scalar_one()

            if actual_database != TEST_DATABASE_NAME:
                raise RuntimeError(
                    f"Unsafe test database: {actual_database}"
                )

    except Exception:
        engine.dispose()
        raise

    yield engine

    engine.dispose()


# ============================================================
# 2. OUTER TRANSACTION
# ============================================================

@pytest.fixture
def db_connection(test_engine):

    connection = test_engine.connect()
    outer_transaction = connection.begin()

    try:
        yield connection

    finally:

        if outer_transaction.is_active:
            outer_transaction.rollback()

        connection.close()


# ============================================================
# 3. SQLALCHEMY TEST SESSION
# ============================================================

@pytest.fixture
def db_session(db_connection):

    session = Session(
        bind=db_connection,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session

    finally:
        session.close()


# ============================================================
# 4. FASTAPI INTEGRATION TEST CLIENT
# ============================================================

@pytest.fixture
def integration_client(db_connection):

    original_overrides = app.dependency_overrides.copy()

    def override_get_db():

        session = Session(
            bind=db_connection,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session

        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    try:

        with TestClient(app) as client:
            yield client

    finally:

        app.dependency_overrides.clear()

        app.dependency_overrides.update(
            original_overrides
        )


# ============================================================
# 5. TEMPORARY DOCUMENT INTEGRATION TEST ACCOUNTS
# ============================================================

@pytest.fixture
def document_test_accounts(db_session):

    from types import SimpleNamespace
    from datetime import date

    from app.models.department import Department
    from app.models.employee import Employee
    from app.models.user import User
    from app.models.role import Role
    from app.models.user_role import UserRole

    # --------------------------------------------------------
    # CREATE TEMPORARY DEPARTMENT
    # --------------------------------------------------------

    department = Department(
        department_name="Document Integration Testing",
        department_code="DOC-TEST",
        is_active=True,
    )

    db_session.add(department)
    db_session.flush()

    # --------------------------------------------------------
    # CREATE EMPLOYEE
    # --------------------------------------------------------

    employee = Employee(
        full_name="Document Test Employee",
        email="document.employee@example.test",
        department="Integration Testing",
        department_id=department.department_id,
        job_title="Test Employee",
        hire_date=date(2020, 1, 1),
        is_active=True,
    )

    # --------------------------------------------------------
    # CREATE HR EMPLOYEE
    # --------------------------------------------------------

    hr_employee = Employee(
        full_name="Document Test HR",
        email="document.hr@example.test",
        department="Integration Testing",
        department_id=department.department_id,
        job_title="HR Officer",
        hire_date=date(2020, 1, 1),
        is_active=True,
    )

    db_session.add_all([employee, hr_employee])
    db_session.flush()

    # --------------------------------------------------------
    # CREATE EMPLOYEE USER
    # --------------------------------------------------------

    employee_user = User(
        employee_id=employee.employee_id,
        email="document.employee.user@example.test",
        password_hash="integration-test-only",
        is_active=True,
    )

    # --------------------------------------------------------
    # CREATE HR USER
    # --------------------------------------------------------

    hr_user = User(
        employee_id=hr_employee.employee_id,
        email="document.hr.user@example.test",
        password_hash="integration-test-only",
        is_active=True,
    )

    db_session.add_all([employee_user, hr_user])
    db_session.flush()

    # --------------------------------------------------------
    # ASSIGN EXISTING ROLES
    # --------------------------------------------------------

    employee_role = (
        db_session.query(Role)
        .filter(Role.role_name == "employee")
        .one()
    )

    hr_role = (
        db_session.query(Role)
        .filter(Role.role_name == "hr")
        .one()
    )

    db_session.add_all([
        UserRole(
            user_id=employee_user.user_id,
            role_id=employee_role.role_id,
        ),
        UserRole(
            user_id=hr_user.user_id,
            role_id=hr_role.role_id,
        ),
    ])

    db_session.flush()

    return SimpleNamespace(
        department=department,
        employee=employee,
        employee_user=employee_user,
        hr_employee=hr_employee,
        hr_user=hr_user,
    )
