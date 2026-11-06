
import bz2
import xml.etree.ElementTree as ET
from pathlib import Path


def read_articles(file_path, limit=None):
    """Read Wikipedia articles without loading the entire XML into RAM."""
    file_path = Path(file_path)
    opener = bz2.open if file_path.suffix == ".bz2" else open

    with opener(file_path, "rb") as handle:
        events = ET.iterparse(handle, events=("start", "end"))
        _, root = next(events)
        count = 0

        for event, element in events:
            if event != "end" or element.tag.rsplit("}", 1)[-1] != "page":
                continue

            namespace = element.findtext("{*}ns", default="")
            title = element.findtext("{*}title", default="")
            wiki_id = element.findtext("{*}id", default="")
            revision = element.find("{*}revision")

            wikitext = (
                revision.findtext("{*}text", default="")
                if revision is not None
                else ""
            )

            if namespace == "0" and title and wikitext:
                if not wikitext.lstrip().lower().startswith("#redirect"):
                    yield wiki_id, title, wikitext
                    count += 1

            element.clear()
            root.clear()

            if limit is not None and count >= limit:
                break
