# Test code developed with ChatGPT assistance.
from flask.testing import FlaskClient
import pytest

def test_create_book(
    client: FlaskClient, reader: tuple[str, str]
) -> None:
    """Create a book and confirm it can be retrieved at its Location."""
    book_data = {
        "title": "The Hunger Games",
        "author": "Suzanne Collins",
        "pages": 374,
        "status": "want_to_read",
    }

    response = client.post(
        "/books",
        json=book_data,
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 201
    book = response.get_json()

    for field, value in book_data.items():
        assert book[field] == value

    assert book["id"] > 0
    assert book["owner_id"] > 0
    assert book["rating"] is None
    assert book["notes"] == ""
    assert response.headers["Location"] == f"/books/{book['id']}"

    saved_response = client.get(
        response.headers["Location"],
        base_url="https://localhost",
    )

    assert saved_response.status_code == 200
    assert saved_response.get_json() == book

def test_update_book(
    client: FlaskClient, reader: tuple[str, str], book: dict
) -> None:
    """Update selected fields while preserving the rest of the saved book."""
    changes = {"status": "reading", "notes": "Started chapter one."}

    response = client.patch(
        f"/books/{book['id']}",
        json=changes,
        auth=reader,
        base_url="https://localhost",
    )

    expected = {**book, **changes}
    assert response.status_code == 200
    assert response.get_json() == expected

    saved_response = client.get(
        f"/books/{book['id']}",
        base_url="https://localhost",
    )
    assert saved_response.status_code == 200
    assert saved_response.get_json() == expected

def test_delete_book(
    client: FlaskClient, reader: tuple[str, str], book: dict
) -> None:
    """Allow the owner to delete a book and confirm it no longer exists."""
    response = client.delete(
        f"/books/{book['id']}",
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "message": "Book deleted successfully"
    }

    saved_response = client.get(
        f"/books/{book['id']}",
        base_url="https://localhost",
    )

    assert saved_response.status_code == 404
    assert saved_response.get_json() == {"message": "Book not found"}

@pytest.mark.parametrize("method", ["PATCH", "DELETE"])
def test_non_owner_cannot_modify_book(
    client: FlaskClient, book: dict, method: str
) -> None:
    """Reject changes from another user and preserve the original book."""
    registration = client.post(
        "/register",
        json={"username": "other_reader", "password": "Reading456!"},
        base_url="https://localhost",
    )
    assert registration.status_code == 201

    response = client.open(
        f"/books/{book['id']}",
        method=method,
        auth=("other_reader", "Reading456!"),
        json={"status": "finished"},
        base_url="https://localhost",
    )

    assert response.status_code == 403
    assert response.get_json() == {"message": "You do not own this book"}

    saved_response = client.get(
        f"/books/{book['id']}",
        base_url="https://localhost",
    )

    assert saved_response.status_code == 200
    assert saved_response.get_json() == book

@pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
@pytest.mark.parametrize(
    "credentials",
    [
        None,
        ("test_reader", "WrongPassword!"),
        ("unknown_reader", "Reading123!"),
    ],
)
def test_book_operations_require_authentication(
    client: FlaskClient,
    book: dict,
    method: str,
    credentials: tuple[str, str] | None,
) -> None:
    """Reject missing credentials, wrong passwords, and unknown users."""
    path = "/books" if method == "POST" else f"/books/{book['id']}"

    response = client.open(
        path,
        method=method,
        auth=credentials,
        json={
            "title": "Another Book",
            "author": "Test Author",
            "pages": 100,
            "status": "reading",
        },
        base_url="https://localhost",
    )

    assert response.status_code == 401
    assert response.get_json() == {"message": "Invalid credentials"}

    saved_response = client.get(
        f"/books/{book['id']}",
        base_url="https://localhost",
    )
    assert saved_response.get_json() == book

    listed_response = client.get(
        "/books",
        base_url="https://localhost",
    )
    assert listed_response.get_json() == [book]

@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
@pytest.mark.parametrize("book_id", [0, -1, 999, 2**63])
def test_missing_book(
    client: FlaskClient,
    reader: tuple[str, str],
    method: str,
    book_id: int,
) -> None:
    """Return a JSON 404 for nonexistent or out-of-range book IDs."""
    response = client.open(
        f"/books/{book_id}",
        method=method,
        auth=reader,
        json={"status": "reading"},
        base_url="https://localhost",
    )

    assert response.status_code == 404
    assert response.get_json() == {"message": "Book not found"}

def test_list_books_filters_by_status(
    client: FlaskClient, reader: tuple[str, str], book: dict
) -> None:
    """Return all books or only those matching the requested status."""
    response = client.post(
        "/books",
        json={
            "title": "Another Book",
            "author": "Test Author",
            "pages": 100,
            "status": "reading",
        },
        auth=reader,
        base_url="https://localhost",
    )
    assert response.status_code == 201
    reading_book = response.get_json()

    all_books = client.get("/books", base_url="https://localhost")
    assert all_books.status_code == 200
    assert all_books.get_json() == [book, reading_book]

    filtered = client.get(
        "/books?status=reading",
        base_url="https://localhost",
    )
    assert filtered.status_code == 200
    assert filtered.get_json() == [reading_book]

    no_matches = client.get(
        "/books?status=finished",
        base_url="https://localhost",
    )
    assert no_matches.status_code == 200
    assert no_matches.get_json() == []


@pytest.mark.parametrize(
    "changes",
    [
        {},
        {"title": "   "},
        {"title": "a" * 201},
        {"author": 123},
        {"pages": 0},
        {"pages": "100"},
        {"pages": True},
        {"status": "unknown"},
        {"status": []},
        {"rating": 6},
        {"rating": True},
        {"notes": "a" * 2001},
        {"notes": None},
        {"owner_id": 2},
        {"id": 99},
        {"unexpected_field": "hello"},
        [],
    ],
)
def test_invalid_book_update(
    client: FlaskClient,
    reader: tuple[str, str],
    book: dict,
    changes: object,
) -> None:
    """Reject invalid updates without changing the saved book."""
    response = client.patch(
        f"/books/{book['id']}",
        json=changes,
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data["message"], str)
    assert data["message"].strip()

    saved_response = client.get(
        f"/books/{book['id']}",
        base_url="https://localhost",
    )
    assert saved_response.status_code == 200
    assert saved_response.get_json() == book

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "Only a title"},
        {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 100,
        },
        {
            "title": "Test Book",
            "author": "Test Author",
            "pages": -1,
            "status": "reading",
        },
        {
            "title": "Test Book",
            "author": "Test Author",
            "pages": 100,
            "status": "reading",
            "owner_id": 999,
        },
        [],
    ],
)
def test_invalid_book_creation(
    client: FlaskClient,
    reader: tuple[str, str],
    payload: object,
) -> None:
    """Reject invalid book data without saving a record."""
    response = client.post(
        "/books",
        json=payload,
        auth=reader,
        base_url="https://localhost",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert isinstance(data["message"], str)
    assert data["message"].strip()

    listed_response = client.get(
        "/books",
        base_url="https://localhost",
    )
    assert listed_response.status_code == 200
    assert listed_response.get_json() == []