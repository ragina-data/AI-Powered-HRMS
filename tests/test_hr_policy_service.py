
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.hr_policy_service import (
    create_policy_with_initial_version,
    submit_policy_for_review,
    approve_policy_version,
    publish_policy_version,
)


# ============================================================
# 1. SUCCESSFUL POLICY CREATION
# ============================================================

def test_create_policy_with_initial_version_success():

    db = MagicMock()
    added_objects = []

    def add_object(obj):
        added_objects.append(obj)

    def flush_objects():
        if len(added_objects) == 1:
            added_objects[0].policy_id = 100

    db.add.side_effect = add_object
    db.flush.side_effect = flush_objects

    policy, policy_version = create_policy_with_initial_version(
        db,
        policy_code=" HR-POL-TEST-001 ",
        policy_title=" Employee Handbook ",
        category=" General HR ",
        description="Test policy description",
        owner_user_id=5,
        created_by_user_id=7,
        version_label="1.0",
        change_summary="Initial policy draft",
    )

    assert policy.policy_code == "HR-POL-TEST-001"
    assert policy.policy_title == "Employee Handbook"
    assert policy.category == "General HR"
    assert policy.description == "Test policy description"
    assert policy.owner_user_id == 5
    assert policy.status == "draft"

    assert policy_version.policy_id == 100
    assert policy_version.version_number == 1
    assert policy_version.version_label == "1.0"
    assert policy_version.status == "draft"
    assert policy_version.created_by_user_id == 7
    assert policy_version.change_summary == "Initial policy draft"

    assert len(added_objects) == 2
    assert db.add.call_count == 2
    assert db.flush.call_count == 2
    db.commit.assert_not_called()


# ============================================================
# 2. SUCCESSFUL POLICY SUBMISSION
# ============================================================

def test_submit_policy_for_review_success():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="draft",
        submitted_at=None,
    )

    chunks = [SimpleNamespace(chunk_id=1)]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        mp.setattr(
            "app.services.hr_policy_service.get_policy_chunks_by_version",
            lambda db, policy_version_id: chunks,
        )

        result = submit_policy_for_review(db, 100)

    assert result.status == "pending_review"
    assert result.submitted_at is not None
    assert result.policy_version_id == 100

    db.flush.assert_called_once()
    db.commit.assert_not_called()


# ============================================================
# 3. REJECT SUBMISSION OF NON-DRAFT POLICY
# ============================================================

def test_submit_policy_for_review_rejects_non_draft():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="pending_review",
        submitted_at=None,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        with pytest.raises(ValueError):
            submit_policy_for_review(db, 100)

    assert policy_version.status == "pending_review"
    db.flush.assert_not_called()
    db.commit.assert_not_called()


# ============================================================
# 4. REJECT SUBMISSION WHEN NO DOCUMENT CHUNKS EXIST
# ============================================================

def test_submit_policy_for_review_rejects_empty_chunks():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="draft",
        submitted_at=None,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        mp.setattr(
            "app.services.hr_policy_service.get_policy_chunks_by_version",
            lambda db, policy_version_id: [],
        )

        with pytest.raises(ValueError):
            submit_policy_for_review(db, 100)

    assert policy_version.status == "draft"
    db.flush.assert_not_called()
    db.commit.assert_not_called()


# ============================================================
# 5. SUCCESSFUL POLICY APPROVAL
# ============================================================

def test_approve_policy_version_success():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="pending_review",
        approved_by_user_id=None,
        approved_at=None,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        result = approve_policy_version(
            db,
            policy_version_id=100,
            approved_by_user_id=7,
        )

    assert result.status == "approved"
    assert result.approved_by_user_id == 7
    assert result.approved_at is not None

    db.flush.assert_called_once()
    db.commit.assert_not_called()


# ============================================================
# 6. REJECT APPROVAL OF NON-PENDING POLICY
# ============================================================

def test_approve_policy_version_rejects_non_pending():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="draft",
        approved_by_user_id=None,
        approved_at=None,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        with pytest.raises(ValueError):
            approve_policy_version(
                db,
                policy_version_id=100,
                approved_by_user_id=7,
            )

    assert policy_version.status == "draft"
    assert policy_version.approved_by_user_id is None
    db.flush.assert_not_called()
    db.commit.assert_not_called()


# ============================================================
# 7. REJECT INVALID APPROVER ID
# ============================================================

def test_approve_policy_version_rejects_invalid_approver():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        status="pending_review",
        approved_by_user_id=None,
        approved_at=None,
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        with pytest.raises(ValueError):
            approve_policy_version(
                db,
                policy_version_id=100,
                approved_by_user_id=0,
            )

    assert policy_version.status == "pending_review"
    assert policy_version.approved_by_user_id is None
    db.flush.assert_not_called()
    db.commit.assert_not_called()


# ============================================================
# 8. SUCCESSFUL FIRST POLICY PUBLICATION
# ============================================================

def test_publish_policy_version_success():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=100,
        policy_id=10,
        status="approved",
        effective_from=None,
        effective_to=None,
        published_at=None,
    )

    policy = SimpleNamespace(
        policy_id=10,
        status="draft",
    )

    db.scalar.return_value = policy
    db.scalars.return_value.all.return_value = []

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        result = publish_policy_version(
            db,
            policy_version_id=100,
            effective_from=date(2026, 12, 1),
        )

    assert result.status == "published"
    assert result.effective_from == date(2026, 12, 1)
    assert result.effective_to is None
    assert result.published_at is not None

    assert policy.status == "published"

    db.flush.assert_called_once()
    db.commit.assert_not_called()


# ============================================================
# 9. CLOSE PREVIOUS OPEN-ENDED POLICY VERSION
# ============================================================

def test_publish_policy_version_closes_previous_version():

    db = MagicMock()

    policy_version = SimpleNamespace(
        policy_version_id=200,
        policy_id=10,
        status="approved",
        effective_from=None,
        effective_to=None,
        published_at=None,
    )

    policy = SimpleNamespace(
        policy_id=10,
        status="published",
    )

    previous_version = SimpleNamespace(
        policy_version_id=100,
        effective_from=date(2026, 1, 1),
        effective_to=None,
        status="published",
    )

    db.scalar.return_value = policy
    db.scalars.return_value.all.return_value = [
        previous_version
    ]

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(
            "app.services.hr_policy_service.validate_policy_version",
            lambda db, policy_version_id: policy_version,
        )

        result = publish_policy_version(
            db,
            policy_version_id=200,
            effective_from=date(2026, 12, 1),
        )

    assert previous_version.effective_to == date(2026, 11, 30)
    assert previous_version.status == "published"

    assert result.status == "published"
    assert result.effective_from == date(2026, 12, 1)

    db.flush.assert_called_once()
    db.commit.assert_not_called()
