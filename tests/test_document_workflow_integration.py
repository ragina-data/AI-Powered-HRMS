
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.employee import Employee

from app.services.document_service import (
    submit_document_request,
    process_document_request,
)

from app.repositories.document_repository import (
    get_document_request_history,
)


def get_active_user_for_role(db, role_name):

    return (
        db.query(User)
        .join(
            UserRole,
            UserRole.user_id == User.user_id,
        )
        .join(
            Role,
            Role.role_id == UserRole.role_id,
        )
        .join(
            Employee,
            Employee.employee_id == User.employee_id,
        )
        .filter(
            Role.role_name == role_name,
            User.is_active.is_(True),
            Employee.is_active.is_(True),
        )
        .order_by(User.user_id)
        .first()
    )


def test_complete_document_request_workflow(db_session):

    # --------------------------------------------------------
    # 1. REUSE EXISTING DEVELOPMENT DATABASE ACCOUNTS
    # --------------------------------------------------------

    employee_user = get_active_user_for_role(
        db_session,
        "employee",
    )

    hr_user = get_active_user_for_role(
        db_session,
        "hr",
    )

    assert employee_user is not None, (
        "No active employee account found in hrms_db"
    )

    assert hr_user is not None, (
        "No active HR account found in hrms_db"
    )

    # --------------------------------------------------------
    # 2. EMPLOYEE SUBMITS REQUEST
    # --------------------------------------------------------

    document_request = submit_document_request(
        db=db_session,
        current_user=employee_user,
        request_data={
            "document_type": "employment_certificate",
            "purpose": "Integration testing",
        },
    )

    assert document_request.status == "pending"

    request_id = document_request.document_request_id

    # --------------------------------------------------------
    # 3. HR APPROVES REQUEST
    # --------------------------------------------------------

    document_request = process_document_request(
        db=db_session,
        document_request_id=request_id,
        processing_data={
            "status": "approved",
            "remarks": "Approved by HR",
        },
        current_user=hr_user,
    )

    assert document_request.status == "approved"

    # --------------------------------------------------------
    # 4. HR STARTS PROCESSING
    # --------------------------------------------------------

    document_request = process_document_request(
        db=db_session,
        document_request_id=request_id,
        processing_data={
            "status": "processing",
            "remarks": "Document preparation started",
        },
        current_user=hr_user,
    )

    assert document_request.status == "processing"

    # --------------------------------------------------------
    # 5. HR COMPLETES DOCUMENT
    # --------------------------------------------------------

    document_request = process_document_request(
        db=db_session,
        document_request_id=request_id,
        processing_data={
            "status": "completed",
            "remarks": "Document issued",
            "document_reference": "INTEGRATION-TEST-001",
        },
        current_user=hr_user,
    )

    assert document_request.status == "completed"

    assert (
        document_request.document_reference
        == "INTEGRATION-TEST-001"
    )

    # --------------------------------------------------------
    # 6. VERIFY TRANSACTION HISTORY
    # --------------------------------------------------------

    history = get_document_request_history(
        db=db_session,
        document_request_id=request_id,
    )

    assert len(history) == 4

    assert [
        record.new_status for record in history
    ] == [
        "pending",
        "approved",
        "processing",
        "completed",
    ]

    assert history[0].previous_status is None
    assert history[1].previous_status == "pending"
    assert history[2].previous_status == "approved"
    assert history[3].previous_status == "processing"

    assert (
        history[0].action_by_user_id
        == employee_user.user_id
    )

    assert all(
        record.action_by_user_id == hr_user.user_id
        for record in history[1:]
    )

    print("Employee ID:", employee_user.employee_id)
    print("HR Employee ID:", hr_user.employee_id)
    print("Document Request ID:", request_id)
    print("Final status:", document_request.status)
    print("History records:", len(history))
    print("Document workflow integration: PASSED")
