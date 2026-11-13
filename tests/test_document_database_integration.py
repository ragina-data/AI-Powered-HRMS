
from sqlalchemy import text


def test_document_integration_uses_isolated_database(db_session):

    database_name = db_session.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert database_name == "hrms_db"


def test_document_tables_exist(db_session):

    expected_tables = {
        "employees",
        "users",
        "hr_document_types",
        "hr_document_requests",
        "hr_document_request_history",
    }

    actual_tables = set(
        db_session.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = current_schema()
                  AND table_type = 'BASE TABLE'
            """)
        ).scalars().all()
    )

    missing_tables = expected_tables - actual_tables

    assert not missing_tables, (
        f"Missing integration test tables: {missing_tables}"
    )


def test_four_document_types_are_available(db_session):

    count = db_session.execute(
        text("""
            SELECT COUNT(*)
            FROM hr_document_types
            WHERE is_active = TRUE
              AND requires_hr_approval = TRUE
        """)
    ).scalar_one()

    assert count == 4
