
import argparse
from pathlib import Path

from indexer import build_index
from preprocess import tokenize
from storage import (
    open_database,
    find_phrase,
    find_term,
    document_title
)

ROOT = Path(__file__).resolve().parent.parent


def choose_xml():
    data = ROOT / "data"

    files = (
        sorted(data.glob("*.xml.bz2"))
        + sorted(data.glob("*.xml"))
    )

    if not files:
        files = sorted(data.glob("*.bz2"))

    if not files:
        raise FileNotFoundError(
            "Put the downloaded Telugu Wikipedia .xml.bz2 "
            "file inside the data folder."
        )

    return files[0]


def main():
    parser = argparse.ArgumentParser(
        description="Telugu positional inverted index"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum Wikipedia articles to read (default: 5000)"
    )

    parser.add_argument(
        "--query",
        help="Find positional postings for one Telugu word"
    )

    parser.add_argument(
        "--phrase",
        help="Find documents containing a Telugu phrase"
    )

    args = parser.parse_args()

    database = ROOT / "index" / "postings.db"

    if args.query is not None or args.phrase is not None:
        if not database.exists():
            parser.error(
                "Index not built. First run: "
                "python src/main.py --limit 5000"
            )

        with open_database(database) as connection:
            if args.query is not None:
                words = tokenize(args.query)

                if len(words) != 1:
                    parser.error(
                        "Use --query with one Telugu word."
                    )

                term = words[0]
                postings = find_term(connection, term)

                cf = sum(len(p) for _, p in postings)
                df = len(postings)

                print(f"TERM: {term}; CF={cf}; DF={df}")

                for doc_id, positions in postings[:50]:
                    title = document_title(connection, doc_id)

                    print(
                        f"Document {doc_id}: {title} "
                        f"| positions={positions}"
                    )

                if len(postings) > 50:
                    print(
                        f"... {len(postings) - 50} more documents"
                    )

            else:
                words = tokenize(args.phrase)
                matches = find_phrase(connection, words)

                print(
                    f"PHRASE: {' '.join(words)}; "
                    f"matching documents={len(matches)}"
                )

                for doc_id, positions in matches[:50]:
                    title = document_title(connection, doc_id)

                    print(
                        f"Document {doc_id}: {title} "
                        f"| starting positions={positions}"
                    )

        return

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    build_index(
        choose_xml(),
        database,
        ROOT / "index" / "vocabulary.tsv",
        ROOT / "output",
        args.limit
    )


if __name__ == "__main__":
    main()
