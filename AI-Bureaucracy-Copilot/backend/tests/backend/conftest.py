import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user
from app.db.models import User
from app.db.session import engine, Base

_mock_user = User(
    id="test-user-system-id",
    email="test_citizen@janseva.gov.in",
    hashed_password="mocked_hashed_password",
)


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    if engine:
        Base.metadata.create_all(bind=engine)


@pytest.fixture(autouse=True)
def override_auth_for_existing_tests(request):
    """
    Automatically override get_current_user for existing test files (unless
    the test file specifically tests authentication, like test_auth_api.py).
    """
    if "test_auth_api" in request.node.fspath.basename:
        # Do not override auth dependency in auth test suite!
        yield
    else:
        app.dependency_overrides[get_current_user] = lambda: _mock_user
        yield
        app.dependency_overrides.pop(get_current_user, None)
