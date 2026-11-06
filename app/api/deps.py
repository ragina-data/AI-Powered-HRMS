from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User


# Extract the JWT access token from the Authorization header.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """
    Validate the JWT and retrieve the active authenticated user.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)

    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")

    if not user_id:
        raise credentials_exception

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        raise credentials_exception

    user = (
        db.query(User)
        .filter(
            User.user_id == user_id,
            User.is_active.is_(True),
        )
        .first()
    )

    if user is None:
        raise credentials_exception

    return user