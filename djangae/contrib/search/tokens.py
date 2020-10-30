from .constants import (
    PUNCTUATION,
    WORD_DOCUMENT_JOIN_STRING,
)


def tokenize_content(content):
    """
        We inherit the rules from the App Engine Search API
        when it comes to punctuation.

        We have a list of punctuation chars which break the
        content into tokens, and then some special cases where it
        makes sense. You can find the rules documented here:
        https://cloud.google.com/appengine/docs/standard/python/search#special-treatment
    """

    tokens = []
    current = ""

    STOP_CHARS = list(PUNCTUATION) + [" "]

    for c in content:
        if c in STOP_CHARS:
            if current.strip():
                tokens.append(current)

            if c.strip() and c != WORD_DOCUMENT_JOIN_STRING:
                tokens.append(c)

            current = ""
        else:
            current += c
    else:
        if current.strip():
            tokens.append(current)

    return tokens
