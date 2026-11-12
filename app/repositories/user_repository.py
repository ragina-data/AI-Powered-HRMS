
"""
User Repository
===============

Purpose:
    Centralize database queries for user accounts and role assignments.

Responsibilities:
    1. Retrieve users by ID, employee ID, and email.
    2. Retrieve existing roles.
    3. Create user accounts.
    4. Assign roles to users.

Transaction management:
    Database commits are handled by the service layer.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole


# ============================================================
# 1. GET USER BY EMPLOYEE ID
# ============================================================

def get_user_by_employee_id(
    db: Session,
    employee_id: int,
) -> User | None:
    """Retrieve the login account linked to an employee."""

    return (
        db.query(User)
        .filter(User.employee_id == employee_id)
        .first()
    )


# ============================================================
# 2. GET USER BY EMAIL
# ============================================================

def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Retrieve a user using a case-insensitive email lookup."""

    normalized_email = email.strip().lower()

    return (
        db.query(User)
        .filter(
            func.lower(User.email) == normalized_email
        )
        .first()
    )


# ============================================================
# 3. GET ROLE BY NAME
# ============================================================

def get_role_by_name(
    db: Session,
    role_name: str,
) -> Role | None:
    """Retrieve an existing role by its name."""

    return (
        db.query(Role)
        .filter(Role.role_name == role_name)
        .first()
    )


# ============================================================
# 4. CREATE USER ACCOUNT
# ============================================================

def create_user_record(
    db: Session,
    user_data: dict,
) -> User:
    """
    Create a new user account and flush it to PostgreSQL.

    Transaction commit is intentionally handled by the service.
    """

    user = User(**user_data)

    db.add(user)
    db.flush()
    db.refresh(user)

    return user


# ============================================================
# 5. ASSIGN ROLE TO USER
# ============================================================

def create_user_role_assignment(
    db: Session,
    user_id: int,
    role_id: int,
) -> UserRole:
    """
    Assign an existing role to a user.

    The composite primary key in user_roles prevents
    duplicate assignments.
    """

    user_role = UserRole(
        user_id=user_id,
        role_id=role_id,
    )

    db.add(user_role)
    db.flush()

    return user_role

# ============================================================
# 1. GET USER BY ID
# ============================================================

def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    """Retrieve a user account by primary key."""

    return (
        db.query(User)
        .filter(User.user_id == user_id)
        .first()
    )
