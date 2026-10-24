from flask import g, request, url_for
from flask_restful import Resource

from cs188_a3 import services
from cs188_a3.app import get_db
from cs188_a3.auth import auth_required
from cs188_a3 import catalog


class Register(Resource):
    """Handle user registration."""

    def post(self) -> tuple[dict[str, str | int], int]:
        """Validate registration details and create a user."""
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return {"message": "Request body must be a JSON object"}, 400

        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not username.strip():
            return {"message": "Username must be nonblank text"}, 400

        if not isinstance(password, str) or not password.strip():
            return {"message": "Password must be nonblank text"}, 400

        if len(password) < 8:
            return {"message": "Password must have at least 8 characters"}, 400

        if len(password.encode("utf-8")) > 72:
            return {"message": "Password must not exceed 72 UTF-8 bytes"}, 400

        user_id = services.register_user(
            get_db(), username.strip(), password
        )

        if user_id is None:
            return {"message": "Username already exists"}, 409

        return {
            "message": "User registered successfully",
            "id": user_id,
        }, 201


class BookList(Resource):
    """Handle listing and creating book records."""

    def get(self) -> tuple[list[dict] | dict, int]:
        """List books, optionally filtered by reading status."""
        status = request.args.get("status")

        try:
            books = services.list_books(get_db(), status)
        except services.ValidationError as error:
            return {"message": str(error)}, 400

        return books, 200

    @auth_required
    def post(self) -> tuple:
        """Create a book owned by the authenticated user."""
        data = request.get_json(silent=True)

        try:
            book = services.create_book(get_db(), g.user_id, data)
        except services.ValidationError as error:
            return {"message": str(error)}, 400

        location = url_for("book_detail", book_id=book["id"])
        return book, 201, {"Location": location}


class BookDetail(Resource):
    """Handle requests for an individual book."""

    def get(self, book_id: int) -> tuple[dict, int]:
        """Return a book, or a 404 response if it does not exist."""
        try:
            book = services.get_book(get_db(), book_id)
        except services.NotFound as error:
            return {"message": str(error)}, 404

        return book, 200

    @auth_required
    def patch(self, book_id: int) -> tuple[dict, int]:
        """Update supplied fields on a book owned by the caller."""
        data = request.get_json(silent=True)

        try:
            book = services.update_book(
                get_db(), g.user_id, book_id, data
            )
        except services.NotFound as error:
            return {"message": str(error)}, 404
        except services.Forbidden as error:
            return {"message": str(error)}, 403
        except services.ValidationError as error:
            return {"message": str(error)}, 400

        return book, 200

    @auth_required
    def delete(self, book_id: int) -> tuple[dict, int]:
        """Delete a book owned by the authenticated caller."""
        try:
            services.delete_book(get_db(), g.user_id, book_id)
        except services.NotFound as error:
            return {"message": str(error)}, 404
        except services.Forbidden as error:
            return {"message": str(error)}, 403

        return {"message": "Book deleted successfully"}, 200


class Catalog(Resource):
    """Search Open Library and import books into the reading list."""

    def get(self) -> tuple:
        """Search the external catalog by title."""
        try:
            books = catalog.search_books(request.args.get("title"))
        except services.ValidationError as error:
            return {"message": str(error)}, 400
        except catalog.ExternalAPIError as error:
            return {"message": str(error)}, 502

        return books, 200

    @auth_required
    def post(self) -> tuple:
        """Import a book by ISBN for the authenticated user."""
        try:
            book = services.import_catalog_book(
                get_db(),
                g.user_id,
                request.get_json(silent=True),
            )
        except services.ValidationError as error:
            return {"message": str(error)}, 400
        except services.NotFound as error:
            return {"message": str(error)}, 404
        except catalog.ExternalAPIError as error:
            return {"message": str(error)}, 502

        location = url_for("book_detail", book_id=book["id"])
        return book, 201, {"Location": location}