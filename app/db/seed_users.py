
import csv
import os
import secrets
from pathlib import Path

from pwdlib import PasswordHash
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.employee import Employee
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole


# Approved privileged account assignments.
ADMIN_EMPLOYEE_CODE = "EMP009"
HR_EMPLOYEE_CODES = {"EMP017", "EMP025"}

MANAGER_JOB_TITLE = "Department Manager"

CREDENTIALS_DIRECTORY = Path("private")
CREDENTIALS_FILE = CREDENTIALS_DIRECTORY / "initial_user_credentials.csv"
TEMPORARY_FILE = CREDENTIALS_DIRECTORY / "initial_user_credentials.tmp"

password_hasher = PasswordHash.recommended()


def determine_role(employee):
    if employee.employee_code == ADMIN_EMPLOYEE_CODE:
        return "admin"

    if employee.employee_code in HR_EMPLOYEE_CODES:
        return "hr"

    if employee.job_title == MANAGER_JOB_TITLE:
        return "manager"

    return "employee"


def seed_users():
    db = SessionLocal()
    temporary_file_created = False

    try:
        # Safety checks: only seed into an empty authentication database.
        existing_users = db.query(User).count()
        existing_assignments = db.query(UserRole).count()

        if existing_users > 0 or existing_assignments > 0:
            raise ValueError(
                "Users or user-role assignments already exist. "
                "Seeding cancelled to protect existing data."
            )

        employees = (
            db.query(Employee)
            .order_by(Employee.employee_id)
            .all()
        )

        if len(employees) != 50:
            raise ValueError(
                f"Expected 50 employees, found {len(employees)}."
            )

        if any(not employee.email for employee in employees):
            raise ValueError("An employee has no email address.")

        if len({employee.email.lower() for employee in employees}) != 50:
            raise ValueError("Employee email addresses are not unique.")

        employee_codes = {
            employee.employee_code for employee in employees
        }

        required_codes = {
            ADMIN_EMPLOYEE_CODE,
            *HR_EMPLOYEE_CODES,
        }

        if not required_codes.issubset(employee_codes):
            raise ValueError(
                "One or more approved Admin/HR employees were not found."
            )

        # Load existing roles. Do not create or modify role definitions.
        roles = {
            role.role_name: role
            for role in db.query(Role).all()
        }

        required_roles = {"admin", "hr", "manager", "employee"}

        if not required_roles.issubset(roles):
            raise ValueError("One or more required roles are missing.")

        # Determine and validate the approved role distribution.
        employee_role_pairs = [
            (employee, determine_role(employee))
            for employee in employees
        ]

        role_counts = {
            role_name: sum(
                assigned_role == role_name
                for _, assigned_role in employee_role_pairs
            )
            for role_name in required_roles
        }

        expected_counts = {
            "admin": 1,
            "hr": 2,
            "manager": 8,
            "employee": 39,
        }

        if role_counts != expected_counts:
            raise ValueError(
                f"Unexpected role distribution: {role_counts}"
            )

        if CREDENTIALS_FILE.exists():
            raise FileExistsError(
                f"{CREDENTIALS_FILE} already exists. "
                "Protect or move the existing credentials before proceeding."
            )

        CREDENTIALS_DIRECTORY.mkdir(exist_ok=True)

        if TEMPORARY_FILE.exists():
            raise FileExistsError(
                f"{TEMPORARY_FILE} already exists. "
                "Inspect it before proceeding."
            )

        credential_rows = []

        # Create users and their role assignments.
        for employee, role_name in employee_role_pairs:
            temporary_password = secrets.token_urlsafe(18)

            user = User(
                employee_id=employee.employee_id,
                email=employee.email,
                password_hash=password_hasher.hash(
                    temporary_password
                ),
                is_active=True,
            )

            db.add(user)
            db.flush()

            assignment = UserRole(
                user_id=user.user_id,
                role_id=roles[role_name].role_id,
            )

            db.add(assignment)

            credential_rows.append({
                "employee_code": employee.employee_code,
                "employee_name": employee.full_name,
                "email": employee.email,
                "role": role_name,
                "temporary_password": temporary_password,
            })

        # Write credentials to a temporary local file.
        with TEMPORARY_FILE.open(
            "x",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "employee_code",
                    "employee_name",
                    "email",
                    "role",
                    "temporary_password",
                ],
            )
            writer.writeheader()
            writer.writerows(credential_rows)

        temporary_file_created = True

        # Commit all 50 users and role assignments together.
        db.commit()

        # Keep the generated credentials in the private directory.
        os.replace(TEMPORARY_FILE, CREDENTIALS_FILE)
        temporary_file_created = False

        print("=" * 55)
        print("USER SEEDING COMPLETED")
        print("=" * 55)
        print(f"Users created: {len(credential_rows)}")
        print(f"Admin accounts: {role_counts['admin']}")
        print(f"HR accounts: {role_counts['hr']}")
        print(f"Manager accounts: {role_counts['manager']}")
        print(f"Employee accounts: {role_counts['employee']}")
        print("Password hashing: Argon2")
        print(f"Credentials file: {CREDENTIALS_FILE}")

        print("\nIMPORTANT:")
        print("Keep the credentials file private.")
        print("Do not commit or share it publicly.")

    except (SQLAlchemyError, ValueError, OSError) as error:
        db.rollback()

        if temporary_file_created and TEMPORARY_FILE.exists():
            TEMPORARY_FILE.unlink()

        print("User seeding failed.")
        print(f"Reason: {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_users()
