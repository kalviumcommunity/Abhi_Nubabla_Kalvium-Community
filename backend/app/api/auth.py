"""
Authentication API Router.

Exposes user signup, user login, admin login, and user session endpoints.
Uses Supabase PostgreSQL database for credential storage and issues backend-signed JWT tokens.
Fully compatible with Next.js frontend services/api.ts.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from app.db.supabase import supabase_db
from app.config import setup_logger

logger = setup_logger("auth_api")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class UserSignupRequest(BaseModel):
    full_name: str
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse


@router.post("/signup", response_model=AuthResponse)
async def signup(req: UserSignupRequest):
    """Registers a new user and issues a backend JWT token."""
    try:
        res = await supabase_db.signup_user(
            email=req.email,
            password=req.password,
            full_name=req.full_name,
            role="user"
        )
        return AuthResponse(
            access_token=res["access_token"],
            user=res["user"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Signup error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Signup failed due to internal error.")


@router.post("/login", response_model=AuthResponse)
async def login(req: UserLoginRequest):
    """Authenticates standard user against stored credentials and issues backend JWT."""
    try:
        res = await supabase_db.login_user(email=req.email, password=req.password)
        return AuthResponse(
            access_token=res["access_token"],
            user=res["user"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed.")


@router.post("/admin/login", response_model=AuthResponse)
async def admin_login(req: AdminLoginRequest):
    """Authenticates administrator user."""
    try:
        res = await supabase_db.login_user(email=req.email, password=req.password)
        user_role = res["user"].get("role", "user")
        if user_role != "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: Admin credentials required.")
        
        return AuthResponse(
            access_token=res["access_token"],
            user=res["user"]
        )
    except HTTPException:
        raise
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(ve))
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Admin authentication failed.")


@router.get("/me")
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Validates backend JWT session token and returns active user profile."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header.")
    
    token = authorization.split(" ")[1]
    user = await supabase_db.get_user_from_token(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token.")
    
    return {"user": user}
