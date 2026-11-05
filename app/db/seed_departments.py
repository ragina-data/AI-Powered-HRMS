
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import SessionLocal
from app.models.department import Department


DEPARTMENTS = [
    {"department_name": "Human Resources", "department_code": "HR"},
    {"department_name": "Finance", "department_code": "FIN"},
    {"department_name": "Information Technology", "department_code": "IT"},
    {"department_name": "Administration", "department_code": "ADMIN"},
    {"department_name": "Sales", "department_code": "SALES"},
    {"department_name": "Marketing", "department_code": "MKT"},
    {"department_name": "Operations", "department_code": "OPS"},
    {"department_name": "Customer Service", "department_code": "CS"},
]


def seed_departments():
    db = SessionLocal()

    try:
        inserted_count = 0
        existing_count = 0

        for department_data in DEPARTMENTS:
            existing_department = (
                db.query(Department)
                .filter(
                    Department.department_name
                    == department_data["department_name"]
                )
                .first()
            )

            if existing_department:
                existing_count += 1
                continue

            existing_code = (
                db.query(Department)
                .filter(
                    Department.department_code
                    == department_data["department_code"]
                )
                .first()
            )

            if existing_code:
                raise ValueError(
                    f"Department code already exists: "
                    f"{department_data['department_code']}"
                )

            department = Department(
                department_name=department_data["department_name"],
                department_code=department_data["department_code"],
                is_active=True,
            )

            db.add(department)
            inserted_count += 1

        db.commit()

        print("=" * 55)
        print("DEPARTMENT SEEDING COMPLETED")
        print("=" * 55)
        print(f"New departments inserted: {inserted_count}")
        print(f"Already existing departments: {existing_count}")
        print(f"Total departments configured: {len(DEPARTMENTS)}")

    except (SQLAlchemyError, ValueError) as error:
        db.rollback()
        print("Department seeding failed.")
        print(f"Reason: {error}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_departments()
