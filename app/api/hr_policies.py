
"""
HR Policy Management API
========================

Purpose:
    Create and manage HR policy records and versions.

Security:
    Policy creation requires policy.manage.
    The authenticated HR user is recorded as owner and creator.
"""

from typing import Annotated
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.permissions import require_permission
from app.db.session import get_db
from app.models.user import User

from app.schemas.hr_policy import (
    HRPolicyCreate,
    HRPolicyCreateResponse,
)

from app.services.hr_policy_service import (
    create_policy_with_initial_version,
    submit_policy_for_review,
    approve_policy_version,
    publish_policy_version,
)
from pathlib import Path
from uuid import uuid4

from fastapi import File, UploadFile

from app.services.gemini_client import (
    GeminiClient,
    GeminiClientError,
)
from app.services.hr_policy_service import (
    ingest_policy_document,
)
from app.schemas.hr_policy import (
    HRPolicyIngestionResponse,
)

router = APIRouter(
    prefix="/hr-policies",
    tags=["HR Policy Management"],
)


@router.post(
    "",
    response_model=HRPolicyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_hr_policy(
    policy_data: HRPolicyCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_permission("policy.manage")),
    ],
):
    """
    Create an HR policy and its initial draft version.

    Requires:
        policy.manage
    """

    try:
        policy, version = create_policy_with_initial_version(
            db=db,
            policy_code=policy_data.policy_code,
            policy_title=policy_data.policy_title,
            category=policy_data.category,
            description=policy_data.description,
            owner_user_id=current_user.user_id,
            created_by_user_id=current_user.user_id,
            version_label=policy_data.version_label,
            change_summary=policy_data.change_summary,
        )

        db.commit()

        return {
            "policy_id": policy.policy_id,
            "policy_code": policy.policy_code,
            "policy_title": policy.policy_title,
            "category": policy.category,
            "status": policy.status,
            "policy_version_id": version.policy_version_id,
            "version_number": version.version_number,
            "version_label": version.version_label,
            "version_status": version.status,
        }

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A policy with this code or version already exists.",
        ) from exc

    except Exception:
        db.rollback()
        raise

@router.post(
    "/{policy_version_id}/document",
    response_model=HRPolicyIngestionResponse,
    status_code=status.HTTP_200_OK,
)
def upload_policy_document(
    policy_version_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("policy.manage")
    ),
):
    """
    Upload and ingest a PDF or DOCX document
    into an existing draft policy version.

    Requires:
        policy.manage
    """

    if policy_version_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy version ID.",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A filename is required.",
        )

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()

    if extension not in {".pdf", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported.",
        )

    # Maximum upload size: 20 MB.
    max_file_size = 20 * 1024 * 1024

    project_root = Path(__file__).resolve().parents[2]
    storage_dir = project_root / "storage" / "policies"
    storage_dir.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}_{original_name}"
    file_path = storage_dir / stored_filename

    client = None

    try:
        total_size = 0

        with file_path.open("wb") as destination:
            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_file_size:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Policy document exceeds the 20 MB limit.",
                    )

                destination.write(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The uploaded document is empty.",
            )

        client = GeminiClient()

        chunks_created = ingest_policy_document(
            db=db,
            policy_version_id=policy_version_id,
            file_path=file_path,
            gemini_client=client,
        )

        db.commit()

        return HRPolicyIngestionResponse(
            policy_version_id=policy_version_id,
            source_file_name=stored_filename,
            chunks_created=chunks_created,
            status="draft",
        )

    except HTTPException:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    except ValueError as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except GeminiClientError as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Policy document embedding failed.",
        ) from exc

    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Policy document ingestion failed.",
        ) from exc

    finally:
        if client is not None:
            client.close()


@router.post(
    "/{policy_version_id}/submit",
    status_code=status.HTTP_200_OK,
)
def submit_hr_policy_for_review(
    policy_version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("policy.manage")
    ),
):
    """
    Submit a draft HR policy version for review.

    Requires:
        policy.manage
    """

    if policy_version_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy version ID.",
        )

    try:
        policy_version = submit_policy_for_review(
            db=db,
            policy_version_id=policy_version_id,
        )

        db.commit()

        return {
            "message": "Policy submitted for review successfully.",
            "policy_version_id": policy_version.policy_version_id,
            "status": policy_version.status,
            "submitted_at": policy_version.submitted_at,
        }

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{policy_version_id}/approve",
    status_code=status.HTTP_200_OK,
)
def approve_hr_policy(
    policy_version_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("policy.manage")
    ),
):
    """
    Approve an HR policy version pending review.

    Requires:
        policy.manage
    """

    if policy_version_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy version ID.",
        )

    try:
        policy_version = approve_policy_version(
            db=db,
            policy_version_id=policy_version_id,
            approved_by_user_id=current_user.user_id,
        )

        db.commit()

        return {
            "message": "Policy approved successfully.",
            "policy_version_id": policy_version.policy_version_id,
            "status": policy_version.status,
            "approved_by_user_id": policy_version.approved_by_user_id,
            "approved_at": policy_version.approved_at,
        }

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise


@router.post(
    "/{policy_version_id}/publish",
    status_code=status.HTTP_200_OK,
)
def publish_hr_policy(
    policy_version_id: int,
    effective_from: date,
    effective_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("policy.manage")
    ),
):
    """
    Publish an approved HR policy version.

    Requires:
        policy.manage
    """

    if policy_version_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid policy version ID.",
        )

    try:
        policy_version = publish_policy_version(
            db=db,
            policy_version_id=policy_version_id,
            effective_from=effective_from,
            effective_to=effective_to,
        )

        db.commit()

        return {
            "message": "Policy published successfully.",
            "policy_version_id": policy_version.policy_version_id,
            "status": policy_version.status,
            "effective_from": policy_version.effective_from,
            "effective_to": policy_version.effective_to,
            "published_at": policy_version.published_at,
        }

    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise
