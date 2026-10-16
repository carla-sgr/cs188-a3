from functools import wraps
from typing import Any, Callable

from flask import g, request

from cs188_a3.app import get_db
from cs188_a3.services import authenticate_user


def auth_required(function: Callable) -> Callable:
    """Require valid HTTP Basic credentials before calling the endpoint."""
    @wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Check credentials and make the authenticated user's ID available."""
        authorization = request.authorization

        if (
            authorization is None
            or authorization.type.lower() != "basic"
            or not authorization.username
            or not authorization.password
        ):
            return (
                {"message": "Invalid credentials"},
                401,
                {"WWW-Authenticate": 'Basic realm="Reading List"'},
            )

        user_id = authenticate_user(
            get_db(),
            authorization.username,
            authorization.password,
        )

        if user_id is None:
            return (
                {"message": "Invalid credentials"},
                401,
                {"WWW-Authenticate": 'Basic realm="Reading List"'},
            )

        g.user_id = user_id
        return function(*args, **kwargs)

    return wrapper