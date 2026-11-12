
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from app.models.user_role import UserRole


def require_role(*allowed_roles: str):
    """
    Restrict access to users with at least one of the specified roles.
    """

    def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:

        user_roles = {
            user_role.role.role_name
            for user_role in current_user.user_roles
        }

        if not user_roles.intersection(allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role",
            )

        return current_user

    return role_checker


def require_permission(*required_permissions: str):
    """
    Restrict access to users who have at least one of the specified permissions.
    """

    def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db: Annotated[Session, Depends(get_db)],
    ) -> User:

        user_permissions = (
            db.query(Permission.permission_code)
            .join(
                RolePermission,
                Permission.permission_id == RolePermission.permission_id,
            )
            .join(
                Role,
                Role.role_id == RolePermission.role_id,
            )
            .join(
                UserRole,
                UserRole.role_id == Role.role_id,
            )
            .filter(UserRole.user_id == current_user.user_id)
            .distinct()
            .all()
        )

        permission_codes = {
            permission[0] for permission in user_permissions
        }

        if not permission_codes.intersection(required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permission",
            )

        return current_user

    return permission_checker

def user_has_permission(
    db: Session,
    user_id: int,
    permission_code: str,
) -> bool:
    """
    Check whether a user has a specific permission
    through any of their assigned roles.
    """

    result = (
        db.query(Permission.permission_id)
        .join(
            RolePermission,
            Permission.permission_id == RolePermission.permission_id,
        )
        .join(
            Role,
            Role.role_id == RolePermission.role_id,
        )
        .join(
            UserRole,
            UserRole.role_id == Role.role_id,
        )
        .filter(
            UserRole.user_id == user_id,
            Permission.permission_code == permission_code,
        )
        .first()
    )

    return result is not None