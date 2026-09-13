import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, engine, Base
from app.db.models import User
from app.services.profile_service import clear_profiles_for_testing
from app.services.document_service import clear_document_store_for_testing
from app.services.automation_service import clear_automation_runs_for_testing

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    if engine:
        Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_test_data():
    clear_profiles_for_testing()
    clear_document_store_for_testing()
    clear_automation_runs_for_testing()
    # Clean users created during test runs
    if SessionLocal:
        db = SessionLocal()
        try:
            db.query(User).filter(User.email.like("%test%@example.com")).delete(synchronize_session=False)
            db.commit()
        finally:
            db.close()
    yield


def test_auth_signup_success():
    payload = {
        "email": "test_citizen1@example.com",
        "password": "Password@123",
    }
    response = client.post("/api/auth/signup", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test_citizen1@example.com"
    assert "id" in data["user"]


def test_auth_signup_duplicate_email():
    payload = {
        "email": "test_duplicate@example.com",
        "password": "Password@123",
    }
    res1 = client.post("/api/auth/signup", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/signup", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["error"]


def test_auth_login_success():
    # Register user first
    signup_payload = {
        "email": "test_login@example.com",
        "password": "SecretPassword123",
    }
    client.post("/api/auth/signup", json=signup_payload)

    # Now login
    login_payload = {
        "email": "test_login@example.com",
        "password": "SecretPassword123",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test_login@example.com"


def test_auth_login_wrong_password():
    signup_payload = {
        "email": "test_wrong_pwd@example.com",
        "password": "CorrectPassword123",
    }
    client.post("/api/auth/signup", json=signup_payload)

    login_payload = {
        "email": "test_wrong_pwd@example.com",
        "password": "WrongPassword456",
    }
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["error"]


def test_unauthenticated_request_rejected():
    # Attempting to access profile without token must fail with 401
    response = client.get("/api/profile/some-id")
    assert response.status_code == 401

    # Schemes discover without token must fail with 401
    res_disc = client.get("/api/schemes/discover?state=Andhra%20Pradesh")
    assert res_disc.status_code == 401


def test_auth_me_with_valid_token():
    signup_payload = {
        "email": "test_me@example.com",
        "password": "MySecretPass123",
    }
    res = client.post("/api/auth/signup", json=signup_payload)
    token = res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "test_me@example.com"


def test_cross_user_isolation():
    # User A
    user_a_res = client.post("/api/auth/signup", json={"email": "test_user_a@example.com", "password": "PasswordA123"})
    token_a = user_a_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    user_b_res = client.post("/api/auth/signup", json={"email": "test_user_b@example.com", "password": "PasswordB123"})
    token_b = user_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates citizen profile
    profile_payload = {
        "name": "Citizen User A",
        "age": 30,
        "gender": "Male",
        "state": "Maharashtra",
        "district": "Pune",
    }
    create_res = client.post("/api/profile", json=profile_payload, headers=headers_a)
    assert create_res.status_code == 201
    profile_a_id = create_res.json()["profile_id"]

    # User A can access their profile
    get_res_a = client.get(f"/api/profile/{profile_a_id}", headers=headers_a)
    assert get_res_a.status_code == 200
    assert get_res_a.json()["name"] == "Citizen User A"

    # User B cannot access User A's profile (403 Forbidden)
    get_res_b = client.get(f"/api/profile/{profile_a_id}", headers=headers_b)
    assert get_res_b.status_code == 403
    assert "forbidden" in get_res_b.json()["error"].lower()
