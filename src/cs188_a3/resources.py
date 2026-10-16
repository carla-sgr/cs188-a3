from flask import request
from flask_restful import Resource

from cs188_a3 import services
from cs188_a3.app import get_db


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