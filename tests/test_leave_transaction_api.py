
import csv
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app


def test_employee_can_retrieve_own_leave_transactions():

    client = TestClient(app)
    access_token = None

    try:
        # 1. Read test credentials.

        with open(
            "private/initial_user_credentials.csv",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            credentials = next(csv.DictReader(file))

        # 2. Authenticate.

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": credentials["email"],
                "password": credentials["temporary_password"],
            },
        )

        assert login_response.status_code == 200, (
            login_response.text
        )

        access_token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # 3. Identify authenticated employee.

        me_response = client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert me_response.status_code == 200

        employee_id = me_response.json()["employee_id"]

        # 4. Retrieve annual leave accrual history.

        response = client.get(
            "/api/v1/leaves/transactions",
            headers=headers,
            params={
                "transaction_type": "accrual",
                "leave_type": "annual",
                "balance_year": 2026,
                "skip": 0,
                "limit": 100,
            },
        )

        assert response.status_code == 200, response.text

        transactions = response.json()

        assert isinstance(transactions, list)

        # 5. Validate response fields.

        for transaction in transactions:

            assert transaction["employee_id"] is not None
            assert transaction["leave_balance_id"] is not None
            assert transaction["transaction_type"] == "accrual"
            assert Decimal(str(transaction["days_delta"])) > 0
            assert transaction["created_at"] is not None

        # 6. Verify EMP001's known accrual transaction.

        if employee_id == 1:

            employee_transaction = next(
                (
                    transaction
                    for transaction in transactions
                    if transaction["employee_id"] == 1
                ),
                None,
            )

            assert employee_transaction is not None

            assert Decimal(
                str(employee_transaction["days_delta"])
            ) == Decimal("25")

        print("Authenticated employee ID:", employee_id)
        print("Retrieved transactions:", len(transactions))
        print("Transaction History API: PASSED")

    finally:

        # 7. Revoke test login session.

        if access_token:

            logout_response = client.post(
                "/api/v1/auth/logout",
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
            )

            assert logout_response.status_code == 200

        client.close()
