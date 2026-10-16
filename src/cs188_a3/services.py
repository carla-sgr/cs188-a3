from flask_bcrypt import Bcrypt

from cs188_a3.db import Database


VALID_STATUSES = {"want_to_read", "reading", "finished"}


class ValidationError(ValueError):
    """Raised when submitted data is invalid."""


class NotFound(Exception):
    """Raised when a requested record does not exist."""


class Forbidden(Exception):
    """Raised when a user tries to change another user's record."""


def register_user(database: Database, username: str, password: str) -> int | None:
    """Hash the password and return the new user's ID, or None for a duplicate."""
    hashed_password = Bcrypt().generate_password_hash(password).decode("utf-8")
    return database.add_user(username, hashed_password)

def authenticate_user(
    database: Database, username: str, password: str
) -> int | None:
    """Return the user's ID if credentials are valid, otherwise None."""
    user = database.get_user(username)

    if user is None:
        return None

    user_id, hashed_password = user

    if len(password.encode("utf-8")) > 72:
        return None

    if not Bcrypt().check_password_hash(hashed_password, password):
        return None

    return user_id


def validate_book_data(data: object, partial: bool = False) -> dict:
    """Validate book fields and return cleaned values."""
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object")

    allowed_fields = {"title", "author", "pages", "status", "rating", "notes"}

    if set(data) - allowed_fields:
        raise ValidationError("Request contains unknown or server-controlled fields")

    if not data:
        raise ValidationError("Provide at least one book field")

    if not partial:
        required_fields = {"title", "author", "pages", "status"}
        if required_fields - set(data):
            raise ValidationError("Title, author, pages, and status are required")

    cleaned = dict(data)

    for field in ("title", "author"):
        if field in cleaned:
            value = cleaned[field]
            if not isinstance(value, str) or not value.strip():
                raise ValidationError(f"{field} must be nonblank text")
            value = value.strip()
            if len(value) > 200:
                raise ValidationError(f"{field} must not exceed 200 characters")
            cleaned[field] = value

    if "pages" in cleaned:
        pages = cleaned["pages"]
        if type(pages) is not int or not 1 <= pages <= 100000:
            raise ValidationError("Pages must be an integer from 1 to 100000")

    if "status" in cleaned:
        status = cleaned["status"]
        if not isinstance(status, str) or status not in VALID_STATUSES:
            raise ValidationError(
                "Status must be want_to_read, reading, or finished"
            )

    if "rating" in cleaned:
        rating = cleaned["rating"]
        if rating is not None:
            if type(rating) is not int or not 1 <= rating <= 5:
                raise ValidationError("Rating must be an integer from 1 to 5 or null")

    if "notes" in cleaned:
        notes = cleaned["notes"]
        if not isinstance(notes, str) or len(notes) > 2000:
            raise ValidationError("Notes must be text of at most 2000 characters")

    if not partial:
        cleaned.setdefault("rating", None)
        cleaned.setdefault("notes", "")

    return cleaned


def create_book(database: Database, owner_id: int, data: object) -> dict:
    """Validate and save a book belonging to the authenticated user."""
    cleaned = validate_book_data(data)

    book_id = database.add_book(
        owner_id=owner_id,
        title=cleaned["title"],
        author=cleaned["author"],
        pages=cleaned["pages"],
        status=cleaned["status"],
        rating=cleaned["rating"],
        notes=cleaned["notes"],
    )

    return database.get_book(book_id)


def get_book(database: Database, book_id: int) -> dict:
    """Return a book or raise NotFound if it does not exist."""
    if book_id < 1 or book_id > 9223372036854775807:
        raise NotFound("Book not found")

    book = database.get_book(book_id)

    if book is None:
        raise NotFound("Book not found")

    return book

def update_book(
    database: Database,
    user_id: int,
    book_id: int,
    data: object,
) -> dict:
    """Update supplied fields only if the caller owns the book."""
    book = get_book(database, book_id)

    if book["owner_id"] != user_id:
        raise Forbidden("You do not own this book")

    changes = validate_book_data(data, partial=True)
    book.update(changes)

    database.update_book(
        book_id=book_id,
        title=book["title"],
        author=book["author"],
        pages=book["pages"],
        status=book["status"],
        rating=book["rating"],
        notes=book["notes"],
    )

    return book

def delete_book(database: Database, user_id: int, book_id: int) -> None:
    """Delete a book only if the caller owns it."""
    book = get_book(database, book_id)

    if book["owner_id"] != user_id:
        raise Forbidden("You do not own this book")

    database.delete_book(book_id)

def list_books(
    database: Database, status: str | None = None
) -> list[dict]:
    """List books, optionally filtering by a valid reading status."""
    if status is not None:
        if not isinstance(status, str) or status not in VALID_STATUSES:
            raise ValidationError(
                "Status must be want_to_read, reading, or finished"
            )

    return database.list_books(status)
