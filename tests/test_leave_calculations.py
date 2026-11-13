
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.leave import LeaveRequestCreate

from app.services.leave_service import (
    calculate_annual_leave_accrual_target,
    calculate_annual_leave_entitlement,
    calculate_sick_leave_pay_tiers,
    get_employee_service_year_period,
    split_leave_days_by_service_year,
    split_sick_leave_by_probation_and_service_year,
    is_paid_sick_leave_eligible,
)


def test_annual_leave_less_than_six_months():
    result = calculate_annual_leave_entitlement(
        date(2026, 1, 1),
        date(2026, 6, 30),
    )

    assert result["eligible"] is False
    assert result["entitlement_days"] == Decimal("0")


def test_annual_leave_exactly_six_months():
    result = calculate_annual_leave_entitlement(
        date(2026, 1, 1),
        date(2026, 7, 1),
    )

    assert result["eligible"] is True
    assert result["entitlement_days"] == Decimal("12")


def test_annual_leave_more_than_six_months():
    result = calculate_annual_leave_entitlement(
        date(2026, 1, 1),
        date(2026, 7, 2),
    )

    assert result["eligible"] is True
    assert result["entitlement_days"] == Decimal("12")


def test_annual_leave_completed_one_year():
    result = calculate_annual_leave_entitlement(
        date(2026, 1, 1),
        date(2027, 1, 1),
    )

    assert result["entitlement_days"] == Decimal("30")


def test_employee_service_year_period():
    result = get_employee_service_year_period(
        date(2026, 3, 15),
        date(2027, 3, 15),
    )

    assert result["balance_year"] == 2027
    assert result["start_date"] == date(2027, 3, 15)
    assert result["end_date"] == date(2028, 3, 14)


def test_leave_split_across_service_years():
    result = split_leave_days_by_service_year(
        date(2026, 3, 15),
        date(2027, 3, 12),
        date(2027, 3, 18),
    )

    assert result == {
        2026: Decimal("3"),
        2027: Decimal("4"),
    }


def test_sick_leave_probation_split():
    result = split_sick_leave_by_probation_and_service_year(
        date(2026, 1, 1),
        date(2026, 6, 28),
        date(2026, 7, 4),
    )

    assert result[2026]["probation_unpaid_days"] == Decimal("3")
    assert result[2026]["post_probation_days"] == Decimal("4")


def test_sick_leave_probation_eligibility():
    hire_date = date(2026, 1, 1)

    assert is_paid_sick_leave_eligible(
        hire_date,
        date(2026, 6, 30),
    ) is False

    assert is_paid_sick_leave_eligible(
        hire_date,
        date(2026, 7, 1),
    ) is True


def test_sick_leave_pay_tiers():
    result = calculate_sick_leave_pay_tiers(
        Decimal("0"),
        Decimal("20"),
    )

    assert result["full_pay_days"] == Decimal("15")
    assert result["half_pay_days"] == Decimal("5")
    assert result["unpaid_days"] == Decimal("0")


def test_sick_leave_cumulative_pay_tiers():
    result = calculate_sick_leave_pay_tiers(
        Decimal("12"),
        Decimal("10"),
    )

    assert result["full_pay_days"] == Decimal("3")
    assert result["half_pay_days"] == Decimal("7")


def test_sick_leave_90_day_limit():
    with pytest.raises(HTTPException):
        calculate_sick_leave_pay_tiers(
            Decimal("89"),
            Decimal("2"),
        )


def test_medical_certificate_for_sick_leave():
    request = LeaveRequestCreate(
        leave_type="sick",
        start_date=date(2026, 11, 20),
        end_date=date(2026, 11, 21),
        medical_certificate_submitted=True,
    )

    assert request.medical_certificate_submitted is True


def test_medical_certificate_defaults_false():
    request = LeaveRequestCreate(
        leave_type="annual",
        start_date=date(2026, 11, 20),
        end_date=date(2026, 11, 21),
    )

    assert request.medical_certificate_submitted is False


def test_medical_certificate_rejected_for_annual_leave():
    with pytest.raises(ValidationError):
        LeaveRequestCreate(
            leave_type="annual",
            start_date=date(2026, 11, 20),
            end_date=date(2026, 11, 21),
            medical_certificate_submitted=True,
        )
def test_first_service_year_reaches_30_days():
    result = calculate_annual_leave_accrual_target(
        hire_date=date(2026, 1, 1),
        balance_year=2026,
        as_of_date=date(2027, 1, 1),
    )

    assert result == Decimal("30")


# ============================================================
# ANNUAL LEAVE MONTHLY ACCRUAL TESTS
# ============================================================

def test_first_service_year_no_accrual_before_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2026,
        date(2026, 6, 30),
    )

    assert result == Decimal("0")


def test_first_service_year_accrual_at_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2026,
        date(2026, 7, 1),
    )

    assert result == Decimal("12")


def test_first_service_year_seven_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2026,
        date(2026, 8, 1),
    )

    assert result == Decimal("14")


def test_first_service_year_eleven_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2026,
        date(2026, 12, 1),
    )

    assert result == Decimal("22")


def test_first_service_year_reaches_30_days():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2026,
        date(2027, 1, 1),
    )

    assert result == Decimal("30")


def test_second_service_year_monthly_accrual():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2027,
        date(2027, 2, 1),
    )

    assert result == Decimal("2.5")


def test_second_service_year_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2027,
        date(2027, 7, 1),
    )

    assert result == Decimal("15.0")


def test_second_service_year_maximum_entitlement():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1),
        2027,
        date(2028, 1, 1),
    )

    assert result == Decimal("30")

def test_first_service_year_no_accrual_before_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2026, date(2026, 6, 30)
    )
    assert result == Decimal("0")


def test_first_service_year_accrual_at_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2026, date(2026, 7, 1)
    )
    assert result == Decimal("12")


def test_first_service_year_seven_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2026, date(2026, 8, 1)
    )
    assert result == Decimal("14")


def test_first_service_year_eleven_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2026, date(2026, 12, 1)
    )
    assert result == Decimal("22")


def test_second_service_year_monthly_accrual():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2027, date(2027, 2, 1)
    )
    assert result == Decimal("2.5")


def test_second_service_year_six_months():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2027, date(2027, 7, 1)
    )
    assert result == Decimal("15.0")


def test_second_service_year_maximum_entitlement():
    result = calculate_annual_leave_accrual_target(
        date(2026, 1, 1), 2027, date(2028, 1, 1)
    )
    assert result == Decimal("30")
