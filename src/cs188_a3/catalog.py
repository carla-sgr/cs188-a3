import re

import requests

from cs188_a3.services import NotFound, ValidationError

# Open Library documentation:
# https://openlibrary.org/dev/docs/api/search
# https://openlibrary.org/dev/docs/api/books
# Implementation developed with ChatGPT assistance.
OPEN_LIBRARY_BASE_URL = "https://openlibrary.org"
REQUEST_TIMEOUT = 30
HEADERS = {
    "User-Agent": "CS188ReadingList/1.0 (carla.segura@drake.edu)"
}


class ExternalAPIError(Exception):
    """Raised when Open Library cannot provide a usable response."""


def request_json(path: str, params: dict) -> dict:
    """Request JSON from Open Library with timeout and error handling."""
    try:
        response = requests.get(
            f"{OPEN_LIBRARY_BASE_URL}{path}",
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise ExternalAPIError(
            "Open Library is unavailable. Please try again later."
        ) from error
    except ValueError as error:
        raise ExternalAPIError(
            "Open Library returned invalid JSON."
        ) from error

    if not isinstance(data, dict):
        raise ExternalAPIError("Open Library returned an unexpected response.")

    return data


def search_books(title: str) -> list[dict]:
    """Search Open Library for up to five matching books."""
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("A nonblank title is required")

    if len(title.strip()) > 200:
        raise ValidationError("Title must not exceed 200 characters")

    data = request_json(
        "/search.json",
        {
            "title": title.strip(),
            "limit": 5,
            "fields": "key,title,author_name,isbn",
        },
    )

    books = data.get("docs")
    if not isinstance(books, list):
        raise ExternalAPIError("Open Library returned unexpected search results.")

    if not all(isinstance(book, dict) for book in books):
        raise ExternalAPIError("Open Library returned invalid book records.")

    return books


def lookup_book(isbn: str) -> dict:
    """Look up a book by ISBN and return its available reading-list fields."""
    if not isinstance(isbn, str):
        raise ValidationError("ISBN must be text")

    isbn = isbn.replace("-", "").replace(" ", "").upper()
    if re.fullmatch(r"(?:[0-9]{13}|[0-9]{9}[0-9X])", isbn) is None:
        raise ValidationError("ISBN must contain 10 or 13 valid characters")

    key = f"ISBN:{isbn}"
    data = request_json(
        "/api/books",
        {"bibkeys": key, "format": "json", "jscmd": "data"},
    )

    if key not in data:
        raise NotFound("No Open Library book found for that ISBN")

    book = data[key]
    if not isinstance(book, dict):
        raise ExternalAPIError("Open Library returned an invalid book record.")

    authors = book.get("authors", [])
    if not isinstance(authors, list):
        authors = []

    names = [
        author["name"]
        for author in authors
        if isinstance(author, dict)
        and isinstance(author.get("name"), str)
        and author["name"].strip()
    ]

    return {
        "title": book.get("title"),
        "author": ", ".join(names),
        "pages": book.get("number_of_pages"),
    }