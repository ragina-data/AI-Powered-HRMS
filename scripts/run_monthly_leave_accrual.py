
"""
Monthly Annual Leave Accrual Job

Execution modes:
    --dry-run : Preview without modifying the database.
    --execute : Perform actual monthly accrual.
"""

import argparse
import logging
import os
import sys

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


# ============================================================
# LOGGING
# ============================================================

LOG_DIRECTORY = PROJECT_ROOT / "logs"
LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIRECTORY / "annual_leave_accrual.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)


# ============================================================
# ARGUMENT PARSER
# ============================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description="HRMS monthly annual leave accrual"
    )

    execution_group = parser.add_mutually_exclusive_group(
        required=True
    )

    execution_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview accrual without modifying the database.",
    )

    execution_group.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual annual leave accrual.",
    )

    return parser


# ============================================================
# MAIN EXECUTION
# ============================================================

def main(argv=None) -> int:

    args = build_parser().parse_args(argv)

    from app.db.session import SessionLocal

    as_of_date = datetime.now(
        ZoneInfo("Asia/Dubai")
    ).date()

    db = None

    try:

        db = SessionLocal()

        logger.info("=" * 60)
        logger.info("MONTHLY ANNUAL LEAVE ACCRUAL JOB")
        logger.info("Calculation date: %s", as_of_date)

        # ----------------------------------------------------
        # DRY-RUN MODE
        # ----------------------------------------------------

        if args.dry_run:

            from app.services.leave_service import (
                preview_annual_leave_accrual_for_all_active_employees,
            )

            result = preview_annual_leave_accrual_for_all_active_employees(
                db=db,
                as_of_date=as_of_date,
                batch_size=100,
            )

            logger.info("MODE: DRY RUN")
            logger.info("Database modified: False")

            logger.info(
                "Active employees: %s",
                result["total_active_employees"],
            )

            logger.info(
                "Employees previewed: %s",
                result["employees_previewed"],
            )

            logger.info(
                "Future hires skipped: %s",
                result["future_hires_skipped"],
            )

            logger.info(
                "Missing hire dates: %s",
                result["missing_hire_dates_skipped"],
            )

            logger.info(
                "Manual review required: %s",
                result["manual_review_required"],
            )

            logger.info(
                "Proposed additional credits: %s days",
                result["total_proposed_credit_days"],
            )

            logger.info(
                "DRY RUN COMPLETED - NO DATABASE CHANGES"
            )

            return 0

        # ----------------------------------------------------
        # ACTUAL EXECUTION MODE
        # ----------------------------------------------------

        from app.services.leave_service import (
            accrue_annual_leave_for_all_active_employees,
        )

        logger.info("MODE: ACTUAL EXECUTION")

        result = accrue_annual_leave_for_all_active_employees(
            db=db,
            as_of_date=as_of_date,
            batch_size=100,
        )

        logger.info(
            "Active employees: %s",
            result["total_active_employees"],
        )

        logger.info(
            "Successfully processed: %s",
            result["total_processed"],
        )

        logger.info(
            "Failed employees: %s",
            result["total_failed"],
        )

        logger.info(
            "Future hires skipped: %s",
            result["future_hires_skipped"],
        )

        for error in result["employee_errors"]:

            logger.error(
                "Employee %s failed: %s",
                error["employee_id"],
                error["error"],
            )

        logger.info("ANNUAL LEAVE ACCRUAL FINISHED")

        return 1 if result["total_failed"] > 0 else 0

    except Exception:

        logger.exception(
            "Annual leave accrual job failed"
        )

        return 1

    finally:

        if db is not None:
            db.close()

            logger.info("Database session closed")

        logger.info("=" * 60)


if __name__ == "__main__":
    raise SystemExit(main())
