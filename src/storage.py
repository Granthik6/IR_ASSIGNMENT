
import sqlite3
from pathlib import Path


def create_database(database_path):
    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    if database_path.exists():
        database_path.unlink()

    connection = sqlite3.connect(database_path)

    connection.executescript("""
        CREATE TABLE documents (
            doc_id INTEGER PRIMARY KEY,
            wiki_id TEXT NOT NULL,
            title TEXT NOT NULL,
            token_count INTEGER NOT NULL
        );

        CREATE TABLE postings (
            term TEXT NOT NULL,
            doc_id INTEGER NOT NULL,
            tf INTEGER NOT NULL,
            positions TEXT NOT NULL,
            PRIMARY KEY (term, doc_id)
        ) WITHOUT ROWID;
    """)

    return connection


def open_database(database_path):
    return sqlite3.connect(database_path)


def add_document(
    connection, doc_id, wiki_id,
    title, token_count, positions_by_term
):
    connection.execute(
        "INSERT INTO documents VALUES (?, ?, ?, ?)",
        (doc_id, wiki_id, title, token_count)
    )

    connection.executemany(
        """
        INSERT INTO postings
        (term, doc_id, tf, positions)
        VALUES (?, ?, ?, ?)
        """,
        (
            (
                term,
                doc_id,
                len(positions),
                ",".join(map(str, positions))
            )
            for term, positions in positions_by_term.items()
        )
    )


def find_term(connection, term):
    rows = connection.execute(
        """
        SELECT doc_id, positions
        FROM postings
        WHERE term = ?
        ORDER BY doc_id
        """,
        (term,)
    )

    return [
        (
            doc_id,
            [int(n) for n in positions.split(",")]
        )
        for doc_id, positions in rows
    ]


def find_phrase(connection, words):
    if not words:
        return []

    term_postings = [
        dict(find_term(connection, word))
        for word in words
    ]

    shared_documents = set(term_postings[0])

    for posting in term_postings[1:]:
        shared_documents.intersection_update(posting)

    matches = []

    for doc_id in sorted(shared_documents):
        starts = set(term_postings[0][doc_id])

        for offset, posting in enumerate(
            term_postings[1:], start=1
        ):
            next_positions = set(posting[doc_id])

            starts = {
                position for position in starts
                if position + offset in next_positions
            }

            if not starts:
                break

        if starts:
            matches.append((doc_id, sorted(starts)))

    return matches


def document_title(connection, doc_id):
    row = connection.execute(
        "SELECT title FROM documents WHERE doc_id = ?",
        (doc_id,)
    ).fetchone()

    return row[0] if row else "Unknown"
