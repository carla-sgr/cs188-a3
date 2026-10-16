from flask.testing import FlaskClient
import pytest


def test_register_success(client: FlaskClient) -> None:
    """A valid registration creates a user without exposing credentials."""
    response = client.post(
        "/register",
        json={
            "username": "test_reader",
            "password": "Reading123!",
        },
        base_url="https://localhost",
    )

    assert response.status_code == 201

    data = response.get_json()
    assert data["message"] == "User registered successfully"
    assert isinstance(data["id"], int)
    assert data["id"] > 0
    assert set(data) == {"message", "id"}


def test_register_duplicate_username(client: FlaskClient) -> None:
    """Reject an existing username even when a different password is supplied."""
    first_response = client.post(
        "/register",
        json={"username": "test_reader", "password": "Reading123!"},
        base_url="https://localhost",
    )
    assert first_response.status_code == 201

    response = client.post(
        "/register",
        json={"username": "test_reader", "password": "Different456!"},
        base_url="https://localhost",
    )

    assert response.status_code == 409
    assert response.get_json() == {"message": "Username already exists"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"username": "reader"},
        {"password": "Reading123!"},
        {"username": "   ", "password": "Reading123!"},
        {"username": "reader", "password": "   "},
        {"username": "reader", "password": "short"},
        {"username": 123, "password": "Reading123!"},
        {"username": "reader", "password": 12345678},
        {"username": "reader", "password": "a" * 73},
        [],
    ],
)
def test_register_invalid_input(
    client: FlaskClient, payload: object
) -> None:
    """Reject invalid registration data with a descriptive JSON error."""
    response = client.post(
        "/register",
        json=payload,
        base_url="https://localhost",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data["message"], str)
    assert data["message"].strip()