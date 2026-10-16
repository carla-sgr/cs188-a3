from flask_bcrypt import Bcrypt

from cs188_a3.db import Database


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