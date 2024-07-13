
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, StaticPool, create_engine

from src.database.db import get_session
from src.main import app
from src.utils.security_utils import check_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///testing.sqlite",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_register_user(client: TestClient):
    register_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
    }
    response = client.post("/users/register", json=register_data)
    assert response.status_code == 201
    data = response.json()
    assert type(UUID(data['id'])) == UUID
    assert data['username'] == register_data["username"]
    assert data['email'] == register_data["email"]
    assert check_password(register_data["password"], data['password']) is True


@pytest.mark.asyncio
async def test_register_user_with_existing_username(client: TestClient):
    register_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
    }
    response = client.post("/users/register", json=register_data)
    assert response.status_code == 409
    assert response.json() == {"detail": "Username already exists"}

headers = None
@pytest.mark.asyncio
async def test_login_user(client: TestClient):
    response = client.post("/users/login", auth=('test_user', 'test_password'))
    assert response.status_code == 200
    assert 'Authorization' in response.headers
    global headers
    headers = {'Authorization': response.headers['Authorization']}


@pytest.mark.asyncio
async def test_login_user_bad_credentials(client: TestClient):
    username = "test_user_bad"
    password = "test_password_bad"
    response = client.post("/users/login", auth=(username, password))
    assert response.status_code == 401
    assert 'Authorization' not in response.headers
    assert response.json() == {'detail': 'Bad credentials'}


@pytest.mark.asyncio
async def test_logout(client: TestClient):
    assert headers is not None
    response = client.post("/users/logout", headers=headers)
    assert response.status_code == 200
    assert 'Authorization' not in response.headers
    assert response.content.decode('utf-8') == 'Logout successful'
