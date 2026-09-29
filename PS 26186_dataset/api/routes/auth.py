from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.config import logger
from core.security import hash_password, verify_password, create_access_token
from core.organization import validate_battalion, validate_location
from db.session import get_db
from db.models.user import User
from db.models.personnel import Personnel
from schemas.auth import (
    UserRegister,
    CommanderSignup,
    JawanSignup,
    UserLogin,
    Token,
    UserOut
)
from api.deps import get_current_user, require_roles

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])

@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user (Admin restricted)"
)
def register(
    user_in: UserRegister,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin"))
):
    """
    Administrative user provisioning endpoint.
    Restricted to system administrators.
    """
    clean_username = user_in.username.strip()
    existing_user = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_in.username}' is already registered."
        )

    # If personnel_id is supplied, verify that the personnel record exists
    if user_in.personnel_id is not None:
        personnel_rec = db.query(Personnel).filter(Personnel.id == user_in.personnel_id).first()
        if not personnel_rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked personnel record ID {user_in.personnel_id} not found."
            )

    battalion_val = None
    location_val = None
    if user_in.battalion:
        try:
            battalion_val = validate_battalion(user_in.battalion)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    if user_in.location:
        try:
            location_val = validate_location(user_in.location)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    hashed_pw = hash_password(user_in.password)
    new_user = User(
        username=clean_username,
        hashed_password=hashed_pw,
        role=user_in.role,
        personnel_id=user_in.personnel_id,
        battalion=battalion_val,
        location=location_val,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    logger.info(f"New user registered: '{new_user.username}' with role '{new_user.role}'")
    return new_user


@router.post(
    "/register-commander",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Self-register a new Commander/Officer account with organizational scope"
)
def register_commander(signup_data: CommanderSignup, db: Session = Depends(get_db)):
    """
    Self-registration endpoint for Commanding Officers.
    Strictly assigns role 'officer' (never allows client-chosen role).
    Binds the account permanently to a validated canonical Battalion and Location scope.
    Returns signed JWT token with scope claims.
    """
    clean_username = signup_data.username.strip()

    # 1. Validate organizational scope against canonical options
    try:
        clean_battalion = validate_battalion(signup_data.battalion)
        clean_location = validate_location(signup_data.location)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 2. Check duplicate username
    existing_user = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Service username '{signup_data.username}' is already registered."
        )

    try:
        hashed_pw = hash_password(signup_data.password)
        new_commander = User(
            username=clean_username,
            hashed_password=hashed_pw,
            role="officer",  # Strictly server-enforced role
            personnel_id=None,
            battalion=clean_battalion,
            location=clean_location,
            is_active=True
        )
        db.add(new_commander)
        db.commit()
        db.refresh(new_commander)
        logger.info(
            f"Self-registered Commander: '{new_commander.username}' assigned to scope '{clean_battalion} • {clean_location}'"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering commander: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account creation. Please try again."
        )

    access_token = create_access_token(
        data={
            "sub": new_commander.username,
            "role": new_commander.role,
            "personnel_id": new_commander.personnel_id,
            "battalion": new_commander.battalion,
            "location": new_commander.location
        }
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=new_commander.role,
        username=new_commander.username,
        personnel_id=new_commander.personnel_id,
        battalion=new_commander.battalion,
        location=new_commander.location
    )


@router.post(
    "/register-jawan",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Self-register a new Jawan account with associated personnel record"
)
def register_jawan(signup_data: JawanSignup, db: Session = Depends(get_db)):
    """
    Self-registration endpoint for personnel.
    Atomically creates a new Personnel record and links it to a new User with role 'personnel'.
    Enforces uniqueness of username and personnel_code, and validates canonical battalion and location.
    Returns an immediate signed JWT token for seamless session initialization.
    """
    clean_username = signup_data.username.strip()
    clean_code = signup_data.personnel_code.strip().upper()

    # 1. Validate organizational scope
    try:
        clean_battalion = validate_battalion(signup_data.battalion)
        clean_location = validate_location(signup_data.location)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # 2. Check duplicate username and existing personnel
    existing_user = db.query(User).filter(func.lower(User.username) == clean_username.lower()).first()
    existing_personnel = db.query(Personnel).filter(func.upper(Personnel.personnel_code) == clean_code).first()

    try:
        if existing_personnel:
            # Allow personnel claiming / updating profile
            target_personnel = existing_personnel
            target_personnel.name = signup_data.name.strip()
            target_personnel.age = signup_data.age
            target_personnel.gender = signup_data.gender
            target_personnel.department = signup_data.department.strip()
            target_personnel.job_role = signup_data.job_role.strip()
            target_personnel.battalion = clean_battalion
            target_personnel.location = clean_location
            target_personnel.experience_years = signup_data.experience_years
            if signup_data.duty_hours_per_week:
                target_personnel.duty_hours_per_week = signup_data.duty_hours_per_week

            linked_user = db.query(User).filter(User.personnel_id == target_personnel.id).first()
            hashed_pw = hash_password(signup_data.password)

            if existing_user:
                if existing_user.personnel_id == target_personnel.id or not existing_user.personnel_id:
                    existing_user.hashed_password = hashed_pw
                    existing_user.battalion = clean_battalion
                    existing_user.location = clean_location
                    existing_user.personnel_id = target_personnel.id
                    existing_user.is_active = True
                    new_user = existing_user
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Service username '{signup_data.username}' is already linked to a different personnel profile."
                    )
            elif linked_user:
                if linked_user.username != clean_username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Personnel code '{signup_data.personnel_code}' is already registered."
                    )
                linked_user.hashed_password = hashed_pw
                linked_user.battalion = clean_battalion
                linked_user.location = clean_location
                linked_user.is_active = True
                new_user = linked_user
            else:
                new_user = User(
                    username=clean_username,
                    hashed_password=hashed_pw,
                    role="personnel",
                    personnel_id=target_personnel.id,
                    battalion=clean_battalion,
                    location=clean_location,
                    is_active=True
                )
                db.add(new_user)
        else:
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Service username '{signup_data.username}' is already registered."
                )

            # Create Personnel record
            target_personnel = Personnel(
                personnel_code=clean_code,
                name=signup_data.name.strip(),
                age=signup_data.age,
                gender=signup_data.gender,
                department=signup_data.department.strip(),
                battalion=clean_battalion,
                job_role=signup_data.job_role.strip(),
                location=clean_location,
                experience_years=signup_data.experience_years,
                duty_hours_per_week=signup_data.duty_hours_per_week or 40.0,
                night_shifts_per_month=0,
                consecutive_duty_days=0,
                transfer_frequency=0,
                training_load=2,
                leave_gap_days=30,
                deployment_days=0,
                remote_posting="No",
                operational_exposure="Low"
            )
            db.add(target_personnel)
            db.flush()

            hashed_pw = hash_password(signup_data.password)
            new_user = User(
                username=clean_username,
                hashed_password=hashed_pw,
                role="personnel",
                personnel_id=target_personnel.id,
                battalion=clean_battalion,
                location=clean_location,
                is_active=True
            )
            db.add(new_user)

        db.commit()
        db.refresh(new_user)
        db.refresh(target_personnel)
        logger.info(
            f"Jawan registration successful: '{new_user.username}' linked to Personnel ID {target_personnel.id} "
            f"({target_personnel.personnel_code}) in '{clean_battalion} • {clean_location}'"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error registering jawan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during account creation. Please try again."
        )

    # 6. Generate and return JWT token with scope claims
    access_token = create_access_token(
        data={
            "sub": new_user.username,
            "role": new_user.role,
            "personnel_id": new_user.personnel_id,
            "battalion": new_user.battalion,
            "location": new_user.location
        }
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=new_user.role,
        username=new_user.username,
        personnel_id=new_user.personnel_id,
        battalion=new_user.battalion,
        location=new_user.location
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and issue JWT token"
)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates username and password, returning a signed JWT Bearer access token
    populated with organizational scope metadata.
    """
    clean_username = login_data.username.strip()
    user = db.query(User).filter(User.username == clean_username).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact system administrator."
        )

    access_token = create_access_token(
        data={
            "sub": user.username,
            "role": user.role,
            "personnel_id": user.personnel_id,
            "battalion": user.battalion,
            "location": user.location
        }
    )

    logger.info(
        f"Successful login for user '{user.username}' (Role: {user.role}, Scope: '{user.battalion}' / '{user.location}')"
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        username=user.username,
        personnel_id=user.personnel_id,
        battalion=user.battalion,
        location=user.location
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Retrieve current authenticated user profile"
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile, RBAC role, and organizational scope.
    """
    return current_user
