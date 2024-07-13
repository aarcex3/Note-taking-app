from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.util.typing import NoneFwd
from sqlmodel import Session, SQLModel, StaticPool, create_engine, select

from src.database.db import get_session
from src.main import app
from src.models.note import NoteModel as Note

registered_user = False
cached_headers = None
post_note_id = None  

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

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def register_user(client: TestClient):
    global registered_user
    if not registered_user:
        client.post("/users/register",
                    json={
                        "username": "test_user2",
                        "email": "test_user2@example.com",
                        "password": "test_password2"
                    })
        registered_user = True


@pytest.fixture
def get_headers(client: TestClient):
    register_user(client)
    global cached_headers
    if cached_headers is None:
        response = client.post("/users/login",
                               auth=('test_user2', 'test_password2'))
        cached_headers = {"Authorization": response.headers['Authorization']}
    return cached_headers


def test_get_no_notes(client: TestClient, get_headers):
    headers = get_headers
    response = client.get('/me/notes', headers=headers)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == 'All notes from test_user2'
    assert data['notes'] == []


def test_post_note(client: TestClient, get_headers):
    headers = get_headers
    global post_note_id
    response = client.post('/me/notes',
                           json={
                               "title": "Test",
                               "content": "Test"
                           },
                           headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data)>= 1 
    assert type(UUID(data['id'])) == UUID
    assert data['title'] == 'Test'
    assert data['content'] == 'Test'
    assert data['created_at'] == datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    assert data['updated_at'] == datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    post_note_id = data['id'] 
    
def test_post_note_wrong_data(client: TestClient, get_headers):
    headers = get_headers
    response = client.post('/me/notes',
                           json={
                               "title": 45,
                               "coft": "Test"
                           },
                           headers=headers)
    assert response.status_code == 422
    assert response.json() == {
        'detail': [{
            'input': 45,
            'loc': ['body', 'title'],
            'msg': 'Input should be a valid string',
            'type': 'string_type'
        }, {
            'input': {
                'coft': 'Test',
                'title': 45
            },
            'loc': ['body', 'content'],
            'msg': 'Field required',
            'type': 'missing'
        }]
    }


def test_get_all_notes(client: TestClient, get_headers):
    headers = get_headers
    response = client.get('/me/notes', headers=headers)
    app.dependency_overrides.clear()
    assert response.status_code == 200
    data = response.json()
    assert data['message'] == 'All notes from test_user2'
    assert len(data['notes']) >= 1

def test_get_note(client: TestClient, get_headers):
    headers = get_headers
    global post_note_id
    response = client.get(f'/me/notes/{post_note_id}', headers=headers)
    data = response.json()
    assert response.status_code == 200
    assert data['id'] ==  post_note_id
    assert data['title']== 'Test'
    assert data['content'] == 'Test'


def test_get_note_wrong_id(client: TestClient, get_headers):
    headers = get_headers
    response = client.get('/me/notes/asfasg', headers=headers)
    assert response.status_code == 422


def test_put_note(client: TestClient, get_headers):
    headers = get_headers
    global post_note_id
    response = client.put(f'/me/notes/{post_note_id}',
                          json={
                              "title": "Updated Test",
                              "content": "Updated Content"
                          },
                          headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == 'Updated Test'
    assert data['content'] == 'Updated Content'
    assert data['updated_at'] == datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")


def test_put_note_wrong_data(client: TestClient, get_headers):
    headers = get_headers
    response = client.put('/me/notes/asdfqwr',
                          json={
                              "tittle": "Updated Test",
                              "content": "Update Test"
                          },
                          headers=headers)
    assert response.status_code == 422


def test_delete_note(client: TestClient,session, get_headers):
    headers = get_headers
    global post_note_id
    response = client.delete(f"/me/notes/{post_note_id}", headers=headers)
    assert response.status_code == 200
    assert response.json() == {'message': f'Note #{post_note_id} deleted'}
    note = session.get(Note,post_note_id)
    assert note is None


def test_delete_note_wrong_id(client: TestClient,session, get_headers):
    headers = get_headers
    global post_note_id
    response = client.delete(f"/me/notes/{post_note_id}", headers=headers)
    assert response.status_code == 404
    assert response.json() == {'detail': 'Note not found'}