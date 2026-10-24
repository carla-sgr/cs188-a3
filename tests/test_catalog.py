import pytest
from flask.testing import FlaskClient

from cs188_a3 import catalog


def test_catalog_search(client: FlaskClient) -> None:
    """Search the real Open Library API through our endpoint."""
    response = client.get(
        "/catalog?title=The%20Hunger%20Games",
        base_url="https://localhost",
    )

    assert response.status_code == 200
    books = response.get_json()
    assert isinstance(books, list)
    assert 1 <= len(books) <= 5
    assert any("hunger games" in book["title"].lower() for book in books)


def test_catalog_import(
    client: FlaskClient, reader: tuple[str, str]
) -> None:
    """Import a real catalog book and verify it was saved."""
    response = client.post(
        "/catalog",
        json={"isbn": "9780980200447"},
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 201
    book = response.get_json()
    assert book["title"].lower() == "slow reading"
    assert book["author"] == "John Miedema"
    assert book["pages"] > 0
    assert book["status"] == "want_to_read"

    saved = client.get(
        response.headers["Location"],
        base_url="https://localhost",
    )
    assert saved.status_code == 200
    assert saved.get_json() == book


@pytest.mark.parametrize("title", ["", "   ", "a" * 201])
def test_catalog_invalid_search(client: FlaskClient, title: str) -> None:
    """Reject invalid search titles before contacting Open Library."""
    response = client.get(
        "/catalog",
        query_string={"title": title},
        base_url="https://localhost",
    )

    assert response.status_code == 400
    assert response.get_json()["message"]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"isbn": "invalid"},
        {"isbn": 9780980200447},
        {"isbn": "9780980200447", "owner_id": 99},
    ],
)
def test_catalog_invalid_import(
    client: FlaskClient, reader: tuple[str, str], payload: dict
) -> None:
    """Reject invalid import requests without saving books."""
    response = client.post(
        "/catalog",
        json=payload,
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 400
    assert response.get_json()["message"]

    saved = client.get("/books", base_url="https://localhost")
    assert saved.get_json() == []


@pytest.mark.parametrize(
    "credentials",
    [None, ("test_reader", "WrongPassword!")],
)
def test_catalog_import_requires_authentication(
    client: FlaskClient,
    reader: tuple[str, str],
    credentials: tuple[str, str] | None,
) -> None:
    """Reject import requests with missing or incorrect credentials."""
    response = client.post(
        "/catalog",
        json={"isbn": "9780980200447"},
        auth=credentials,
        base_url="https://localhost",
    )

    assert response.status_code == 401
    assert response.get_json() == {"message": "Invalid credentials"}


def test_catalog_network_failure(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return a helpful 502 response when the external request times out."""
    def timeout(*args: object, **kwargs: object) -> None:
        """Simulate a timeout without making an external request."""
        raise catalog.requests.exceptions.ReadTimeout("Simulated timeout")

    monkeypatch.setattr(catalog.requests, "get", timeout)

    response = client.get(
        "/catalog?title=Example",
        base_url="https://localhost",
    )

    assert response.status_code == 502
    assert response.get_json() == {
        "message": "Open Library is unavailable. Please try again later."
    }