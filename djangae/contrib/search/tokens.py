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

    new_tokens = []
    indexes_to_remove = []

    # Detect acronyms
    acronym_run = 0
    for i, token in enumerate(tokens):
        if token == "-" and i > 0 and tokens[i - 1] != "-":
            acronym_run += 1
        else:
            if acronym_run > 1 and token != "-":
                start = i - (2 * acronym_run)
                parts = [tokens[start + (x * 2)] for x in range(acronym_run + 1)]
                acronym = "".join(parts)

                # Add variations of the acronym
                new_tokens.append(acronym)
                new_tokens.append(".".join(parts))
                new_tokens.append("-".join(parts))

                indexes_to_remove.extend(range(start, start + (acronym_run * 2) + 1))
                acronym_run = 0
            elif i > 0 and tokens[i - 1] != "-":
                acronym_run = 0

    tokens = [x for i, x in enumerate(tokens) if i not in indexes_to_remove]
    tokens.extend(new_tokens)

    return tokens
