
from collections import defaultdict
from pathlib import Path

from parser import read_articles
from preprocess import tokenize
from storage import (
    add_document,
    create_database,
    find_phrase,
    find_term,
    document_title
)


def build_index(
    xml_path, database_path,
    vocabulary_path, output_path, limit
):
    connection = create_database(database_path)

    # Vocabulary stored in RAM.
    # term -> [Collection Frequency, Document Frequency]
    vocabulary = {}

    first_phrase = None
    document_count = 0

    try:
        for wiki_id, title, raw_text in read_articles(xml_path, limit):
            words = tokenize(raw_text)

            if not words:
                continue

            document_count += 1
            positions_by_term = defaultdict(list)

            for position, word in enumerate(words):
                positions_by_term[word].append(position)

            if first_phrase is None and len(words) >= 2:
                first_phrase = (document_count, words[:2])

            for word, positions in positions_by_term.items():
                stats = vocabulary.setdefault(word, [0, 0])
                stats[0] += len(positions)
                stats[1] += 1

            # Store postings on disk using SQLite.
            add_document(
                connection,
                document_count,
                wiki_id,
                title,
                len(words),
                positions_by_term
            )

            if document_count % 100 == 0:
                connection.commit()

            if document_count % 500 == 0:
                print(f"Indexed {document_count} documents...")

        connection.commit()

        if document_count == 0:
            raise RuntimeError("No Telugu articles could be indexed.")

        vocabulary_path = Path(vocabulary_path)
        vocabulary_path.parent.mkdir(parents=True, exist_ok=True)

        with vocabulary_path.open("w", encoding="utf-8") as file:
            file.write("term\tCF\tDF\n")

            for word in sorted(vocabulary):
                cf, df = vocabulary[word]
                file.write(f"{word}\t{cf}\t{df}\n")

        write_reports(
            connection,
            vocabulary,
            first_phrase,
            output_path,
            document_count
        )

        print(
            f"DONE: {document_count} documents, "
            f"{len(vocabulary)} unique terms"
        )
        print(f"Disk postings: {database_path}")
        print(f"Vocabulary: {vocabulary_path}")
        print(f"Results: {output_path}")

    finally:
        connection.close()


def write_reports(
    connection, vocabulary,
    first_phrase, output_path, document_count
):
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    # Prefer meaningful rare words that start with a Telugu letter.
    # Each selected word occurs exactly once in a different document.
    import unicodedata

    rare_candidates = sorted(
        (term for term, (cf, df) in vocabulary.items()
         if cf == 1 and df == 1 and len(term) >= 6
         and unicodedata.category(term[0]).startswith("L"))
    )

    rare_terms = []
    seen_documents = set()
    for term in rare_candidates:
        matches = find_term(connection, term)
        if not matches:
            continue
        doc_id = matches[0][0]
        if doc_id not in seen_documents:
            rare_terms.append(term)
            seen_documents.add(doc_id)
        if len(rare_terms) == 10:
            break

    if len(rare_terms) != 10:
        raise RuntimeError("Fewer than 10 distinct rare-term examples available")

    # Generate 10 rare-term examples.
    with (output_path / "rare_terms.txt").open(
        "w", encoding="utf-8"
    ) as file:

        file.write(
            "10 RARE TELUGU TERMS WITH COMPLETE POSITIONAL INDEX\n"
        )

        file.write(
            f"Number of indexed documents: {document_count}\n\n"
        )

        for number, term in enumerate(rare_terms, start=1):
            cf, df = vocabulary[term]

            file.write(
                f"EXAMPLE {number}: {term}\n"
                f"CF={cf}, DF={df}\n"
            )

            for doc_id, positions in find_term(connection, term):
                title = document_title(connection, doc_id)

                file.write(
                    f"  doc_id={doc_id}, "
                    f"title={title}, "
                    f"positions={positions}\n"
                )

            file.write("\n")

    checks = []

    # TEST 1: Verify CF and DF.
    frequent = max(
        vocabulary,
        key=lambda word: vocabulary[word][0]
    )

    postings = find_term(connection, frequent)
    cf, df = vocabulary[frequent]

    case1 = (
        sum(len(pos) for _, pos in postings) == cf
        and len(postings) == df
    )

    checks.append((
        case1,
        f"CF/DF check for '{frequent}': CF={cf}, DF={df}"
    ))

    # TEST 2: Verify repeated term positions.
    row = connection.execute(
        """
        SELECT term, doc_id, tf, positions
        FROM postings
        WHERE tf >= 2
        LIMIT 1
        """
    ).fetchone()

    if row:
        term, doc_id, tf, data = row
        positions = [int(x) for x in data.split(",")]

        case2 = (
            tf == len(positions)
            and positions == sorted(set(positions))
        )

        checks.append((
            case2,
            f"Repeated term '{term}', doc_id={doc_id}, "
            f"positions={positions}"
        ))
    else:
        checks.append((
            False,
            "No term with repeated positions was found"
        ))

    # TEST 3: Verify phrase searching.
    if first_phrase:
        sample_doc_id, phrase = first_phrase
        results = find_phrase(connection, phrase)

        case3 = any(
            doc == sample_doc_id and 0 in starts
            for doc, starts in results
        )

        checks.append((
            case3,
            f"Phrase '{' '.join(phrase)}' occurs at "
            f"position 0 in doc_id={sample_doc_id}; "
            f"matches={len(results)}"
        ))
    else:
        checks.append((
            False,
            "No two-word phrase available"
        ))

    # TEST 4: Verify rare term postings.
    if rare_terms:
        rare = rare_terms[0]
        rare_postings = find_term(connection, rare)

        case4 = (
            len(rare_postings) == vocabulary[rare][1]
            and sum(len(pos) for _, pos in rare_postings)
            == vocabulary[rare][0]
        )

        checks.append((
            case4,
            f"Rare term '{rare}', "
            f"CF={vocabulary[rare][0]}, "
            f"DF={vocabulary[rare][1]}, "
            f"postings={rare_postings}"
        ))
    else:
        checks.append((
            False,
            "No rare terms available"
        ))

    # TEST 5: Search for a nonexistent term.
    absent = "ఈపదంఈసేకరణలోలేదుఅనుకోవాలి"

    while absent in vocabulary:
        absent += "లే"

    case5 = find_term(connection, absent) == []

    checks.append((
        case5,
        f"Absent term '{absent}' -> no postings"
    ))

    # Write five test cases.
    with (output_path / "test_cases.txt").open(
        "w", encoding="utf-8"
    ) as file:

        file.write(
            "5 REAL TEST CASES FOR THE TELUGU POSITIONAL INDEX\n"
        )
        file.write(f"Indexed documents: {document_count}\n")
        file.write(f"Vocabulary size: {len(vocabulary)}\n")
        file.write(
            "Positions are 0-based indices of cleaned Telugu tokens.\n\n"
        )

        for number, (passed, description) in enumerate(
            checks, start=1
        ):
            status = "PASS" if passed else "FAIL"

            file.write(f"TEST {number}: {status}\n")
            file.write(description + "\n\n")

    if not all(passed for passed, _ in checks):
        raise RuntimeError(
            "One or more tests failed; see output/test_cases.txt"
        )
