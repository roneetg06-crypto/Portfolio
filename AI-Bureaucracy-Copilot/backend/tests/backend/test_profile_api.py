import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.profile_service import clear_profiles_for_testing

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    clear_profiles_for_testing()


def test_create_citizen_profile_success():
    payload = {
        "name": "Ramesh Kumar",
        "age": 42,
        "gender": "Male",
        "state": "Andhra Pradesh",
        "district": "Visakhapatnam",
    }
    response = client.post("/api/profile", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "profile_id" in data
    assert data["name"] == "Ramesh Kumar"
    assert data["state"] == "Andhra Pradesh"


def test_create_citizen_profile_invalid_age():
    payload = {
        "name": "Invalid Age",
        "age": -5,
        "gender": "Male",
        "state": "Kerala",
        "district": "Ernakulam",
    }
    response = client.post("/api/profile", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


def test_create_citizen_profile_missing_required_field():
    payload = {
        "name": "Missing State",
        "age": 30,
        "gender": "Female",
        "district": "Central",
    }
    response = client.post("/api/profile", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data


def test_get_citizen_profile_success():
    payload = {
        "name": "Anita Roy",
        "age": 35,
        "gender": "Female",
        "state": "Kerala",
        "district": "Thiruvananthapuram",
    }
    create_res = client.post("/api/profile", json=payload)
    profile_id = create_res.json()["profile_id"]

    get_res = client.get(f"/api/profile/{profile_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Anita Roy"


def test_get_citizen_profile_not_found():
    response = client.get("/api/profile/non-existent-uuid")
    assert response.status_code == 404
    assert "error" in response.json()


def test_schemes_discovery_endpoint():
    response = client.get("/api/schemes/discover?state=Andhra%20Pradesh&sector=health")
    assert response.status_code == 200
    schemes = response.json()
    assert isinstance(schemes, list)
    assert len(schemes) >= 4
