import sqlite3


def connect(db_path: str) -> sqlite3.Connection:
    """Open a connection to the database at the given path."""
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


class Database:
    def __init__(self, db_path: str = "reading_list.db") -> None:
        """Connect to the database and create its tables."""
        self.conn = connect(db_path)
        self.create_users_table()
        self.create_books_table()

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


    def create_books_table(self) -> None:
        """Create the books table if it does not already exist."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    pages INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    rating INTEGER,
                    notes TEXT NOT NULL DEFAULT '',
                    FOREIGN KEY (owner_id) REFERENCES users(id)
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


    def add_book(
        self,
        owner_id: int,
        title: str,
        author: str,
        pages: int,
        status: str,
        rating: int | None = None,
        notes: str = "",
    ) -> int:
        """Save a book and return its assigned ID."""
        with self.conn:
            cursor = self.conn.execute(
                """
                INSERT INTO books
                    (owner_id, title, author, pages, status, rating, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (owner_id, title, author, pages, status, rating, notes),
            )
        return cursor.lastrowid

    
    def get_book(self, book_id: int) -> dict | None:
        """Return a book by ID, or None if it does not exist."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(
            """
            SELECT id, owner_id, title, author, pages, status, rating, notes
            FROM books
            WHERE id = ?
            """,
            (book_id,),
        )
        row = cursor.fetchone()

        return dict(row) if row is not None else None


    def list_books(self, status: str | None = None) -> list[dict]:
        """Return all books, optionally filtered by reading status."""
        cursor = self.conn.cursor()
        cursor.row_factory = sqlite3.Row

        if status is None:
            cursor.execute(
                """
                SELECT id, owner_id, title, author, pages, status, rating, notes
                FROM books
                ORDER BY id
                """
            )
        else:
            cursor.execute(
                """
                SELECT id, owner_id, title, author, pages, status, rating, notes
                FROM books
                WHERE status = ?
                ORDER BY id
                """,
                (status,),
            )

        return [dict(row) for row in cursor.fetchall()]


    def update_book(
        self,
        book_id: int,
        title: str,
        author: str,
        pages: int,
        status: str,
        rating: int | None,
        notes: str,
    ) -> bool:
        """Update a book's editable fields and report whether it exists."""
        with self.conn:
            cursor = self.conn.execute(
                """
                UPDATE books
                SET title = ?, author = ?, pages = ?,
                    status = ?, rating = ?, notes = ?
                WHERE id = ?
                """,
                (title, author, pages, status, rating, notes, book_id),
            )
        return cursor.rowcount == 1

    def delete_book(self, book_id: int) -> bool:
        """Delete a book and return whether a record was removed."""
        with self.conn:
            cursor = self.conn.execute(
                "DELETE FROM books WHERE id = ?",
                (book_id,),
            )
        return cursor.rowcount == 1
    

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()