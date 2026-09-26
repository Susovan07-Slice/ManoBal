from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from core.config import settings, logger
from core.security import decode_access_token
from db.session import get_db
from db.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Validates JWT Bearer token and returns the current active User.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    username: Optional[str] = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject identifier.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated.",
        )
        
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory that enforces Role-Based Access Control (RBAC).
    Allowed roles: 'admin', 'officer', 'welfare', 'personnel'.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"Unauthorized access attempt by user '{current_user.username}' "
                f"(Role: {current_user.role}). Required roles: {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of the following roles: {list(allowed_roles)}"
            )
        return current_user
    return role_checker


from db.models.personnel import Personnel

def check_personnel_access(
    current_user: User,
    target_personnel_id: int,
    db: Session
) -> Personnel:
    """
    Ensures organizational scope-based access control:
    - Admin: System-wide broader access.
    - Officer / Welfare: Can ONLY access personnel from their EXACT matching Battalion AND Location.
    - Personnel: Can ONLY access their own linked personnel record.
    """
    personnel = db.query(Personnel).filter(Personnel.id == target_personnel_id).first()
    if not personnel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Personnel record with ID {target_personnel_id} not found."
        )

    # Admin retains system-wide broader access
    if current_user.role == "admin":
        return personnel

    # Officer and Welfare: Scoped strictly to matching Battalion AND Location
    if current_user.role in ["officer", "welfare"]:
        user_battalion = (current_user.battalion or "").strip().lower()
        user_location = (current_user.location or "").strip().lower()
        p_battalion = (personnel.battalion or "").strip().lower()
        p_location = (personnel.location or "").strip().lower()

        # Both Battalion AND Location must match exactly
        if not user_battalion or not user_location or user_battalion != p_battalion or user_location != p_location:
            logger.warning(
                f"Scope Violation: User '{current_user.username}' (Scope: '{current_user.battalion}' / '{current_user.location}') "
                f"attempted to access out-of-scope Personnel ID {target_personnel_id} "
                f"(Scope: '{personnel.battalion}' / '{personnel.location}')"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Target personnel is outside your assigned Battalion and Location scope."
            )
        return personnel

    # Individual personnel: Can only access their own linked record
    if current_user.role == "personnel":
        if current_user.personnel_id != target_personnel_id:
            logger.warning(
                f"RBAC Violation: Personnel user '{current_user.username}' (linked ID: {current_user.personnel_id}) "
                f"attempted to access restricted personnel record ID: {target_personnel_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are only authorized to access your own personnel record."
            )
        return personnel

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: Insufficient authorization level."
    )
