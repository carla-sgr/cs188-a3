from flask import Flask, current_app, g
from flask_restful import Api
from flask_talisman import Talisman
from pathlib import Path

from cs188_a3.db import Database


def get_db() -> Database:
    """Get the database connection for the current request."""
    if "db" not in g:
        g.db = Database(current_app.config["DATABASE_PATH"])
    return g.db


def close_db(error: BaseException | None = None) -> None:
    """Close the database connection after the request."""
    database = g.pop("db", None)
    if database is not None:
        database.close()


def init_api(app: Flask) -> None:
    """Connect API resources to their URLs."""
    from cs188_a3.resources import Register, BookList, BookDetail, Catalog

    api = Api(app)
    api.add_resource(Register, "/register")
    api.add_resource(BookList, "/books")
    api.add_resource(
        BookDetail,
        "/books/<int(signed=True):book_id>",
        endpoint="book_detail",
    )
    api.add_resource(Catalog, "/catalog")


def create_app(db_path: str = "reading_list.db") -> Flask:
    """Create the Flask app with the selected database path."""
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = db_path
    app.config["PREFERRED_URL_SCHEME"] = "https"
    Talisman(app, force_https=True)
    app.teardown_appcontext(close_db)
    init_api(app)
    return app

def run_app() -> None:
    """Run the API locally over HTTPS."""
    project_root = Path(__file__).resolve().parents[2]
    certificate = project_root / "MyCertificate.crt"
    private_key = project_root / "MyKey.pem"

    create_app().run(
        ssl_context=(str(certificate), str(private_key))
    )