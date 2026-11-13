
import csv
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app


def test_employee_can_retrieve_own_leave_balances():

    client = TestClient(app)
    access_token = None

    try:
        # 1. Read existing test credentials.

        with open(
            "private/initial_user_credentials.csv",
            newline="",
            encoding="utf-8-sig",
        ) as file:
            credentials = next(csv.DictReader(file))

        # 2. Authenticate through the actual login API.

        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": credentials["email"],
                "password": credentials["temporary_password"],
            },
        )

        assert login_response.status_code == 200, (
            f"Login failed: {login_response.text}"
        )

        access_token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        # 3. Identify the authenticated employee.

        me_response = client.get(
            "/api/v1/auth/me",
            headers=headers,
        )

        assert me_response.status_code == 200

        employee_id = me_response.json()["employee_id"]

        assert employee_id is not None

        # 4. Retrieve the employee's own leave balances.

        response = client.get(
            "/api/v1/leaves/balances/me",
            headers=headers,
        )

        assert response.status_code == 200, response.text

        balances = response.json()

        assert isinstance(balances, list)

        # 5. Validate every returned balance.

        for balance in balances:

            assert balance["employee_id"] == employee_id

            assert "leave_type" in balance
            assert "entitlement_days" in balance
            assert "used_days" in balance
            assert "available_days" in balance
            assert "balance_year" in balance

            expected_available = (
                Decimal(str(balance["entitlement_days"]))
                - Decimal(str(balance["used_days"]))
            )

            actual_available = Decimal(
                str(balance["available_days"])
            )

            assert actual_available == expected_available

        # 6. Verify EMP001's initialized annual balance
        #    when the authenticated account belongs to EMP001.

        if employee_id == 1:

            annual_balance = next(
                (
                    balance
                    for balance in balances
                    if balance["leave_type"] == "annual"
                    and balance["balance_year"] == 2026
                ),
                None,
            )

            assert annual_balance is not None

            assert Decimal(
                str(annual_balance["entitlement_days"])
            ) == Decimal("25")

            assert Decimal(
                str(annual_balance["available_days"])
            ) == Decimal("25")

        print("Authenticated employee ID:", employee_id)
        print("Returned balance records:", len(balances))
        print("Leave balance API: PASSED")

    finally:
        # 7. Revoke the test login session.

        if access_token:

            logout_response = client.post(
                "/api/v1/auth/logout",
                headers={
                    "Authorization": f"Bearer {access_token}"
                },
            )

            assert logout_response.status_code == 200

        client.close()
