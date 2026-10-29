# Test code developed with ChatGPT assistance.
from collections.abc import Iterator

import pytest
from flask.testing import FlaskClient

from cs188_a3.app import create_app


@pytest.fixture
def client(tmp_path) -> Iterator[FlaskClient]:
    """Provide a test client with a fresh temporary database."""
    app = create_app(db_path=str(tmp_path / "test.db"))
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

@pytest.fixture
def reader(client: FlaskClient) -> tuple[str, str]:
    """Register a test user and return their Basic Auth credentials."""
    credentials = ("test_reader", "Reading123!")

    response = client.post(
        "/register",
        json={
            "username": credentials[0],
            "password": credentials[1],
        },
        base_url="https://localhost",
    )
    assert response.status_code == 201

    return credentials

@pytest.fixture
def book(client: FlaskClient, reader: tuple[str, str]) -> dict:
    """Create a book owned by the test reader."""
    response = client.post(
        "/books",
        json={
            "title": "The Hunger Games",
            "author": "Suzanne Collins",
            "pages": 374,
            "status": "want_to_read",
        },
        auth=reader,
        base_url="https://localhost",
    )
    assert response.status_code == 201
    return response.get_json()