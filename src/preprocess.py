
import html
import re
import unicodedata

TELUGU_TOKEN = re.compile(
    r"[\u0C00-\u0C7F]+(?:[\u200c\u200d][\u0C00-\u0C7F]+)*"
)


def clean_text(wikitext):
    text = re.sub(r"<!--.*?-->", " ", wikitext, flags=re.DOTALL)

    text = re.sub(
        r"<ref\b[^>]*>.*?</ref\s*>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL
    )

    text = re.sub(
        r"<ref\b[^>]*/>", " ", text, flags=re.IGNORECASE
    )

    text = re.sub(r"\{\|.*?\|\}", " ", text, flags=re.DOTALL)

    template = re.compile(r"\{\{[^{}]*\}\}", flags=re.DOTALL)

    for _ in range(30):
        new_text = template.sub(" ", text)
        if new_text == text:
            break
        text = new_text

    def replace_wikilink(match):
        link = match.group(1)

        if link.lower().startswith((
            "file:", "image:", "category:",
            "వర్గం:", "దస్త్రం:", "చిత్రం:"
        )):
            return " "

        return link.split("|")[-1].split("#")[0]

    text = re.sub(
        r"\[\[([^\]]+)\]\]", replace_wikilink, text
    )

    text = re.sub(
        r"\[https?://[^\s\]]+(?:\s+([^\]]+))?\]",
        lambda match: match.group(1) or " ",
        text
    )

    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)

    return html.unescape(text)


def tokenize(wikitext):
    cleaned = unicodedata.normalize("NFC", clean_text(wikitext))
    words = []

    for match in TELUGU_TOKEN.finditer(cleaned):
        word = match.group().strip("\u200c\u200d")

        if any(
            unicodedata.category(char).startswith("L")
            for char in word
        ):
            words.append(word)

    return words
