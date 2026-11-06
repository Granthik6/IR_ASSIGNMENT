# TELUGU POSITIONAL INVERTED INDEX

## INFORMATION RETRIEVAL - ASSIGNMENT 1 (IR-M2026)

- Roll Number: S20240010240
- Language: Telugu
- Language of Implementation: Python 3.11 (supports Python 3.9+)

## OVERVIEW

This project indexes a subset of 5,000 articles from a Telugu Wikipedia
XML dump and constructs a positional inverted index.

## DATA SOURCE

Telugu Wikipedia articles XML dump:
https://dumps.wikimedia.org/tewiki/latest/

Filename: `tewiki-latest-pages-articles-multistream.xml.bz2`

The entire dump is NOT indexed; only the first 5,000 eligible nonempty
articles are processed by the program (the exact subset is defined by the
parsing rules and the downloaded snapshot).

## INDEX STATISTICS (FROM THE SUBMITTED RUN)

- Indexed documents: 5,000
- Unique Telugu terms: 223,744
- Query example: Telugu term 'తెలుగు', CF=5,391, DF=2,348

## DATA STRUCTURE AND MEMORY/DISK REQUIREMENT

The vocabulary is held in RAM as a Python dictionary:

```text
term -> [collection_frequency, document_frequency]
```

Postings are stored on the disk in an SQLite database:

```text
(term, document_id, term_frequency, positions)
```

Positions refer to zero-based offsets in the cleaned, tokenized document.
Each document's positions are held temporarily in RAM and written to disk.
The complete collection postings are NOT held in RAM.

## MODULES

- `src/main.py`: CLI for index building, single-term lookup and phrase search.
- `src/parser.py`: streaming reader for Wikipedia XML / .bz2 archives.
- `src/preprocess.py`: markup removal, NFC normalization, Telugu tokenization.
- `src/indexer.py`: CF/DF computation, posting creation and report generation.
- `src/storage.py`: SQLite schema, document/position storage and retrieval.
- `requirements.txt`: Python version and external dependencies (none).

## HOW TO RUN

1. Install Python 3.9 or newer.
2. Download the Telugu Wikipedia pages-articles XML .bz2 dump from
   the Wikimedia link above.
3. Create a folder named `data/` in the repository root and place the
   downloaded .xml.bz2 archive there.
4. Open a terminal in the project root and run:

   ```bash
   python src/main.py --limit 5000
   ```

5. Run a term query:

   ```bash
   python src/main.py --query "తెలుగు"
   ```

6. Run a two-word phrase query:

   ```bash
   python src/main.py --phrase "తెలుగు భాష"
   ```

## FILES PRODUCED BY THE PROGRAM

- `index/postings.db`: disk-backed SQLite postings and document metadata.
- `index/vocabulary.tsv`: vocabulary export (term, CF, DF).
- `output/test_cases.txt`: five executable validation test results.
- `output/rare_terms.txt`: ten rare Telugu terms, CF/DF, and positional postings.

## TESTS

1. Collection Frequency (CF) and Document Frequency (DF) consistency.
2. Multiple occurrences have correctly ordered positions.
3. Correct phrase matches from adjacent word positions.
4. Rare-term posting consistency.
5. An unknown term has no postings.

See `output/test_cases.txt` for the actual run results (five PASS results).
Ten real rare-word examples from this dataset are in `output/rare_terms.txt`.

## REPRODUCIBILITY

The vocabulary and SQLite index are omitted from this small GitHub source
repository ZIP. They can be regenerated using the command above with the
original Wikimedia dump. Different snapshot dates may change the results.

### FULL GENERATED INDEX (OPTIONAL EXTERNAL MIRROR)

https://drive.google.com/drive/folders/1U7sXxASswzKmo9v-5sgLYYtz02ELbdO2?usp=sharing

## NOTES

This repository contains the source code and sample outputs, not the
entire Wikipedia dataset. Both the dataset and the full index are excluded
from the course submission ZIP in accordance with the assignment.
