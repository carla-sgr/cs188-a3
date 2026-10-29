# Reading List API

A Flask API where users manage books, reading progress, ratings, and notes.
Users can search Open Library and import books by ISBN. SQLite stores
users and books, and only a book's owner can update or delete it.

## Getting started

Install uv and Python 3.14 or newer, then run:

```bash
git clone https://github.com/carla-sgr/cs188-a3.git
cd cs188-a3
uv sync --locked --dev
```

Create a local HTTPS certificate from the project directory:

```bash
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout MyKey.pem -out MyCertificate.crt -days 365 \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```

Start the API:

```bash
uv run cs188-a3
```

Base URL: `https://localhost:5000`

The database `reading_list.db` is created automatically. No environment
variables or API keys are required. Certificates, private keys, and
database files must not be committed.

Run tests:

```bash
uv run pytest -q
```

Tests use temporary databases. Catalog integration tests require internet
access and Open Library availability. GitHub Actions also runs the tests.

## Endpoints

Requests with bodies use JSON. Protected requests use HTTP Basic
authentication. Passwords are stored as bcrypt hashes.

| Method and path | Purpose | Authentication | Success | Errors |
| --- | --- | --- | --- | --- |
| POST /register | Create a user | None | 201 | 400, 409 |
| GET /books | List books; optionally filter by status | None | 200 | 400 |
| POST /books | Create a book | Required | 201 | 400, 401 |
| GET /books/<book_id> | Retrieve a book | None | 200 | 404 |
| PATCH /books/<book_id> | Update supplied fields | Owner | 200 | 400, 401, 403, 404 |
| DELETE /books/<book_id> | Delete a book | Owner | 200 | 401, 403, 404 |
| GET /catalog | Search Open Library by title | None | 200 | 400, 502 |
| POST /catalog | Import a book by ISBN | Required | 201 | 400, 401, 404, 502 |

`book_id` is a required integer path parameter identifying a stored book.
Successful book creation and import return the book and a `Location`
header pointing to it.

Errors contain a JSON `message`: 400 means invalid input, 401 invalid or
missing credentials, 403 not the owner, 404 not found, 409 duplicate
username, and 502 an external-service failure.

### Registration body

| Field | Type | Required | Meaning and rules |
| --- | --- | --- | --- |
| username | string | Yes | Account name; cannot be blank |
| password | string | Yes | Account password; nonblank, at least 8 characters, at most 72 UTF-8 bytes |

Registration returns a message and user ID, never a password or hash.

### Book body

For POST, the fields marked required must be supplied. PATCH accepts any
nonempty subset of these fields.

| Field | Type | Required on POST | Meaning and rules |
| --- | --- | --- | --- |
| title | string | Yes | Book title; 1–200 characters after trimming |
| author | string | Yes | Author name; 1–200 characters after trimming |
| pages | integer | Yes | Page count; 1–100000 |
| status | string | Yes | Reading progress: want_to_read, reading, or finished |
| rating | integer or null | No | Personal score, 1–5; defaults to null |
| notes | string | No | Personal notes, at most 2000 characters; defaults to "" |

The server assigns `id` and `owner_id`. Unknown and server-controlled
fields are rejected.

GET /books accepts the optional string query parameter `status`, using
one of the three values above. Without it, all books are returned.

### Catalog parameters

GET /catalog requires the string query parameter `title`: nonblank search
text of at most 200 characters. It returns up to five results.

POST /catalog accepts:

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| isbn | string | Yes | ISBN-10 or ISBN-13; spaces and hyphens are accepted |
| pages | integer | No* | Override the external page count |
| status | string | No | Reading progress; defaults to want_to_read |
| rating | integer or null | No | Personal score; defaults to null |
| notes | string | No | Personal notes; defaults to "" |

*Supply pages when the external record lacks a page count.
Book validation rules also apply to imported books. Title and author
come from Open Library.

The integration calls `/search.json` with a title and `/api/books` with
ISBN lookup parameters. Requests use an identifying User-Agent and a
30-second timeout.

## Example session

With the server running, open another terminal in the project directory.

Register a user — expected 201:

```bash
curl --cacert MyCertificate.crt -i https://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"reader","password":"Reading123!"}'
```

Create a book — expected 201 with the saved book and its ID:

```bash
curl --cacert MyCertificate.crt -i https://localhost:5000/books \
  -u 'reader:Reading123!' \
  -H "Content-Type: application/json" \
  -d '{"title":"The Hunger Games","author":"Suzanne Collins","pages":374,"status":"want_to_read"}'
```

List books — expected 200 with a JSON list:

```bash
curl --cacert MyCertificate.crt -i https://localhost:5000/books
```

Attempt creation without credentials — expected 401:

```bash
curl --cacert MyCertificate.crt -i https://localhost:5000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"Frankenstein","author":"Mary Shelley","pages":280,"status":"want_to_read"}'
```

Error response:

```json
{"message": "Invalid credentials"}
```

## Resources and AI use

- CS 188 API activity and assignment guide: starting patterns for Flask,
  SQLite, authentication, HTTPS, and GitHub Actions.
- Open Library documentation:
  https://openlibrary.org/dev/docs/api/search and
  https://openlibrary.org/dev/docs/api/books.
- ChatGPT: To make sure I didn't miss a step and debugging.