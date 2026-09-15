"""
Unit tests for Backend Custom JWT Authentication and Supabase Credential Storage.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend root directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main_app import create_app
from app.db.supabase import hash_password, verify_password, create_access_token, decode_access_token, supabase_db

app = create_app()
client = TestClient(app)


def test_password_hashing():
    raw_password = "SecretPassword123!"
    hashed = hash_password(raw_password)
    
    assert hashed != raw_password
    assert ":" in hashed
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False
    print("✓ test_password_hashing passed")


def test_jwt_token_generation_and_decoding():
    user_id = "user-12345"
    email = "test@example.com"
    role = "user"
    full_name = "Test User"
    
    token = create_access_token(user_id, email, role, full_name)
    assert isinstance(token, str)
    assert len(token) > 20
    
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert payload["role"] == role
    assert payload["full_name"] == full_name
    print("✓ test_jwt_token_generation_and_decoding passed")


def test_invalid_jwt_token():
    payload = decode_access_token("invalid.jwt.token")
    assert payload is None
    print("✓ test_invalid_jwt_token passed")


def test_signup_and_login_flow():
    email = "newuser@corp.com"
    password = "MySecurePassword123"
    full_name = "Corporate User"
    pwd_hash = hash_password(password)

    # Mock httpx responses for signup, login, and me
    async def mock_get(url, headers=None):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        if "email=eq." in url:
            if "newuser@corp.com" in url:
                # First check for signup (empty), later check for login (found)
                if getattr(mock_get, "signed_up", False):
                    mock_resp.json.return_value = [{
                        "id": "mock-user-123",
                        "email": email,
                        "password_hash": pwd_hash,
                        "full_name": full_name,
                        "role": "user"
                    }]
                else:
                    mock_resp.json.return_value = []
        elif "id=eq." in url:
            mock_resp.json.return_value = [{
                "id": "mock-user-123",
                "email": email,
                "full_name": full_name,
                "role": "user"
            }]
        return mock_resp

    async def mock_post(url, json=None, headers=None):
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = [{"id": "mock-user-123"}]
        mock_get.signed_up = True
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_get), \
         patch("httpx.AsyncClient.post", side_effect=mock_post):

        # 1. Signup
        signup_resp = client.post("/api/auth/signup", json={
            "email": email,
            "password": password,
            "full_name": full_name,
        })
        assert signup_resp.status_code == 200
        data = signup_resp.json()
        assert "access_token" in data
        assert data["user"]["email"] == email
        assert data["user"]["full_name"] == full_name
        assert data["user"]["role"] == "user"
        
        token = data["access_token"]
        
        # 2. Fetch /me
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_resp.status_code == 200
        user_me = me_resp.json()["user"]
        assert user_me["email"] == email
        
        # 3. Login with correct password
        login_resp = client.post("/api/auth/login", json={
            "email": email,
            "password": password,
        })
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data
        
        # 4. Login with wrong password
        wrong_pass_resp = client.post("/api/auth/login", json={
            "email": email,
            "password": "WrongPassword",
        })
        assert wrong_pass_resp.status_code == 401

    print("✓ test_signup_and_login_flow passed")


def test_admin_login():
    admin_email = "admin@corp.com"
    admin_pass = "AdminPass123"
    admin_hash = hash_password(admin_pass)

    async def mock_get(url, headers=None):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{
            "id": "admin-user-id",
            "email": admin_email,
            "password_hash": admin_hash,
            "full_name": "System Admin",
            "role": "admin"
        }]
        return mock_resp

    with patch("httpx.AsyncClient.get", side_effect=mock_get):
        admin_login_resp = client.post("/api/auth/admin/login", json={
            "email": admin_email,
            "password": admin_pass,
        })
        assert admin_login_resp.status_code == 200
        admin_data = admin_login_resp.json()
        assert admin_data["user"]["role"] == "admin"

    print("✓ test_admin_login passed")


if __name__ == "__main__":
    test_password_hashing()
    test_jwt_token_generation_and_decoding()
    test_invalid_jwt_token()
    test_signup_and_login_flow()
    test_admin_login()
    print("\nALL AUTH TESTS PASSED SUCCESSFULLY!")
