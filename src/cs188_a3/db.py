import sqlite3


def connect(db_path: str) -> sqlite3.Connection:
    """Open a connection to the database at the given path."""
    return sqlite3.connect(db_path)


class Database:
    def __init__(self, db_path: str = "reading_list.db") -> None:
        """Connect to the database and create its tables."""
        self.conn = connect(db_path)
        self.create_users_table()

    def create_users_table(self) -> None:
        """Create the users table if it does not already exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
            """)

    def add_user(self, username: str, hashed_pwd: str) -> int | None:
        """Create a user and return their ID, or None if the username exists."""
        try:
            with self.conn:
                cursor = self.conn.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_pwd)
                )
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user(self, username: str) -> tuple[int, str] | None:
        """Return the user's ID and password hash, or None if not found."""
        cursor = self.conn.execute(
            "SELECT id, password FROM users WHERE username = ?",
            (username,)
        )
        return cursor.fetchone()

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()