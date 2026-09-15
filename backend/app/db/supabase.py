"""
Supabase Database Client & Backend JWT Authentication Service.

Stores user credentials directly in Supabase PostgreSQL (public.users table via REST API)
and handles password hashing (PBKDF2-HMAC-SHA256) and JWT token creation/verification in the backend.
"""

import os
import uuid
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import httpx
import jwt

from app.config import AppConfig, setup_logger

logger = setup_logger("supabase_db")


def hash_password(password: str) -> str:
    """Hashes a raw password using PBKDF2-HMAC-SHA256 with a random 16-byte salt."""
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"{salt.hex()}:{pwd_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verifies a raw password against a stored salt:hash string."""
    try:
        parts = stored_hash.split(":")
        if len(parts) != 2:
            return False
        salt = bytes.fromhex(parts[0])
        original_hash = bytes.fromhex(parts[1])
        computed_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return secrets.compare_digest(computed_hash, original_hash)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def create_access_token(user_id: str, email: str, role: str, full_name: str) -> str:
    """Generates a backend-signed JWT access token."""
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=AppConfig.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "full_name": full_name,
        "iat": int(now.timestamp()),
        "exp": int(expiration.timestamp()),
    }
    return jwt.encode(payload, AppConfig.JWT_SECRET, algorithm=AppConfig.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a backend-issued JWT access token."""
    try:
        payload = jwt.decode(token, AppConfig.JWT_SECRET, algorithms=[AppConfig.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


class SupabaseClient:
    """Interface for database user credential operations via Supabase REST API & Backend JWT."""

    def __init__(self):
        self.url = AppConfig.SUPABASE_URL.rstrip("/")
        self.anon_key = AppConfig.SUPABASE_ANON_KEY
        self.service_key = AppConfig.SUPABASE_SERVICE_ROLE_KEY

    def is_configured(self) -> bool:
        return bool(self.url and self.anon_key and self.url != "https://your-project.supabase.co")

    def get_headers(self, use_service_role: bool = True) -> Dict[str, str]:
        key = self.service_key if (use_service_role and self.service_key) else self.anon_key
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    async def signup_user(self, email: str, password: str, full_name: str, role: str = "user") -> Dict[str, Any]:
        """Registers a user by storing credentials directly in public.users table and issuing a backend JWT."""
        if not self.is_configured():
            raise ValueError("Supabase database credentials not configured.")

        pwd_hash = hash_password(password)
        headers = self.get_headers(use_service_role=True)

        async with httpx.AsyncClient() as client:
            # Check if email already exists in 'users' or 'profiles' table
            for table in ("users", "profiles"):
                check_url = f"{self.url}/rest/v1/{table}?email=eq.{email}&select=id"
                resp = await client.get(check_url, headers=headers)
                
                # Check for schema missing table error
                if resp.status_code != 200:
                    err_text = resp.text
                    if "PGRST205" in err_text:
                        if table == "users":
                            continue  # Try profiles next
                        raise ValueError(
                            "Database table 'public.users' was not found in your Supabase project. "
                            "Please execute the SQL script in 'backend/schema.sql' inside your Supabase Dashboard SQL Editor."
                        )
                    if "PGRST204" in err_text:
                        raise ValueError(
                            "Column 'password_hash' was not found in your Supabase database. "
                            "Please run 'backend/schema.sql' in your Supabase SQL Editor to create the public.users table."
                        )

                if resp.status_code == 200:
                    if len(resp.json()) > 0:
                        raise ValueError("User with this email already exists.")

                    user_id = str(uuid.uuid4())
                    insert_url = f"{self.url}/rest/v1/{table}"
                    payload = {
                        "id": user_id,
                        "email": email,
                        "password_hash": pwd_hash,
                        "full_name": full_name,
                        "role": role,
                    }
                    insert_resp = await client.post(insert_url, json=payload, headers=headers)
                    if insert_resp.status_code in (200, 201):
                        access_token = create_access_token(user_id, email, role, full_name)
                        return {
                            "access_token": access_token,
                            "user": {
                                "id": user_id,
                                "email": email,
                                "full_name": full_name,
                                "role": role,
                            }
                        }
                    else:
                        msg = insert_resp.text
                        logger.error(f"Failed to insert user to table '{table}': {msg}")
                        if "PGRST204" in msg:
                            raise ValueError(
                                "Column 'password_hash' missing in database. Please run 'backend/schema.sql' in your Supabase SQL Editor."
                            )
                        raise ValueError(f"Supabase Signup Failed: {msg}")

            raise ValueError(
                "Database table 'public.users' was not found in your Supabase project. "
                "Please execute the SQL script in 'backend/schema.sql' inside your Supabase Dashboard SQL Editor."
            )

    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticates user credentials against stored password hash in public.users and issues a backend JWT."""
        if not self.is_configured():
            raise ValueError("Supabase database credentials not configured.")

        headers = self.get_headers(use_service_role=True)
        async with httpx.AsyncClient() as client:
            for table in ("users", "profiles"):
                user_url = f"{self.url}/rest/v1/{table}?email=eq.{email}&select=*"
                resp = await client.get(user_url, headers=headers)
                if resp.status_code == 200 and resp.json():
                    users = resp.json()
                    user_data = users[0]

                    if not verify_password(password, user_data.get("password_hash", "")):
                        raise ValueError("Invalid email or password.")

                    user_id = user_data["id"]
                    role = user_data.get("role", "user")
                    full_name = user_data.get("full_name") or email.split("@")[0]

                    access_token = create_access_token(user_id, email, role, full_name)
                    return {
                        "access_token": access_token,
                        "user": {
                            "id": user_id,
                            "email": email,
                            "full_name": full_name,
                            "role": role,
                        }
                    }

            raise ValueError("Invalid email or password.")

    async def get_user_from_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validates backend JWT access token and fetches profile from public.users/profiles."""
        payload = decode_access_token(access_token)
        if not payload:
            return None

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role", "user")
        full_name = payload.get("full_name", "")

        if not self.is_configured():
            return {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role,
            }

        headers = self.get_headers(use_service_role=True)
        async with httpx.AsyncClient() as client:
            for table in ("users", "profiles"):
                user_url = f"{self.url}/rest/v1/{table}?id=eq.{user_id}&select=id,email,full_name,role"
                resp = await client.get(user_url, headers=headers)
                if resp.status_code == 200 and resp.json():
                    row = resp.json()[0]
                    return {
                        "id": row.get("id"),
                        "email": row.get("email"),
                        "full_name": row.get("full_name"),
                        "role": row.get("role", "user"),
                    }

        return {
            "id": user_id,
            "email": email,
            "full_name": full_name,
            "role": role,
        }

    async def add_user_history_entry(self, email: str, entry: Dict[str, Any]) -> bool:
        """Appends a new Q&A entry to the user profile JSONB history field in Supabase public.users / public.profiles."""
        if not self.is_configured() or not email:
            return False

        headers = self.get_headers(use_service_role=True)
        async with httpx.AsyncClient() as client:
            for table in ("users", "profiles"):
                get_url = f"{self.url}/rest/v1/{table}?email=eq.{email}&select=id,history"
                try:
                    resp = await client.get(get_url, headers=headers)
                    if resp.status_code == 200 and resp.json():
                        row = resp.json()[0]
                        user_id = row.get("id")
                        current_history = row.get("history") or []
                        if not isinstance(current_history, list):
                            current_history = []

                        updated_history = [entry] + current_history
                        updated_history = updated_history[:50]

                        patch_url = f"{self.url}/rest/v1/{table}?id=eq.{user_id}"
                        patch_resp = await client.patch(
                            patch_url,
                            json={"history": updated_history, "updated_at": datetime.now(timezone.utc).isoformat()},
                            headers=headers
                        )
                        if patch_resp.status_code in (200, 204):
                            logger.info(f"Successfully stored history entry in Supabase '{table}' table for {email}")
                            return True
                except Exception as e:
                    logger.error(f"Error saving user history to Supabase table '{table}': {e}")
        return False

    async def get_user_history(self, email: str) -> List[Dict[str, Any]]:
        """Retrieves past Q&A history list from user profile JSONB history field in Supabase."""
        if not self.is_configured() or not email:
            return []

        headers = self.get_headers(use_service_role=True)
        async with httpx.AsyncClient() as client:
            for table in ("users", "profiles"):
                get_url = f"{self.url}/rest/v1/{table}?email=eq.{email}&select=history"
                try:
                    resp = await client.get(get_url, headers=headers)
                    if resp.status_code == 200 and resp.json():
                        row = resp.json()[0]
                        history = row.get("history")
                        if isinstance(history, list) and history:
                            return history
                except Exception as e:
                    logger.error(f"Error fetching user history from Supabase table '{table}': {e}")
        return []


supabase_db = SupabaseClient()
