from .constants import (
    PUNCTUATION,
    WORD_DOCUMENT_JOIN_STRING,
    SPECIAL_SYMBOLS,
    SPACE,
    EMPTY,
)


def _tokenize_words(content):
    tokens = []
    words = content.split(SPACE)

    for word in words:
        # append word as it is except if it contains WORD_DOCUMENT_JOIN_STRING
        word = word.replace(WORD_DOCUMENT_JOIN_STRING, EMPTY)
        if word != EMPTY:
            tokens.append(word)

            # split on PUNCTUATION
            if not word.isalnum():
                for punct in PUNCTUATION | SPECIAL_SYMBOLS:
                    tokens.extend(word.split(punct))
                    tokens.append(word.replace(punct, EMPTY))
                # append a version of the word stripped by all its symbols
                tokens.append("".join([c for c in word if c.isalnum()]))

    # exclude single char symbols
    tokens = list(filter(lambda x: len(x) > 1 or (len(x) == 1 and x[0].isalnum()), tokens))

    return set(tokens)


def _word_acronyms(token):
    acronyms_list = []
    ACRONYM_TOKENS = {".", "-"}
    letters = list(token)[0::2]
    symbols = list(token)[1::2]
    # if all the symbols are the same and they're in the list of ACRONYM_TOKENS look for acronyms
    if len(set(symbols)) == 1 and symbols[0] in ACRONYM_TOKENS:
        list_of_non_alpha = list(filter(lambda x: not x.isalpha(), letters))
        if len(list_of_non_alpha) == 0:
            symbol_to_replace = symbols[0]
            for symbol in ACRONYM_TOKENS - set(symbols):
                acronyms_list.append(token.replace(symbol_to_replace, symbol))
                acronyms_list.append(token.replace(symbol_to_replace, EMPTY))

    return acronyms_list


def _date_acronyms(token):
    acronyms_list = []
    ACRONYM_TOKENS = {".", "-"}
    date = []
    token_delimiter = None
    found_first_delimiter = False
    for acronym_delimiter in ACRONYM_TOKENS:
        if acronym_delimiter in token:
            if found_first_delimiter:
                # found two delimiters in the same date
                return []
            date = token.split(acronym_delimiter)
            token_delimiter = acronym_delimiter
            found_first_delimiter = True

    # if all the symbols are the same and they're in the list of ACRONYM_TOKENS look for acronyms
    list_of_non_digit = list(filter(lambda x: not x.isdigit(), "".join(date)))
    if len(list_of_non_digit) == 0 and token_delimiter:
        for symbol in ACRONYM_TOKENS - set(token_delimiter):
            acronyms_list.append(token.replace(token_delimiter, symbol))
            acronyms_list.append(token.replace(token_delimiter, EMPTY))

    return acronyms_list


def acronyms(token):
    """
    Return list of tokens when an acronym is detected for a given token.

    Acronyms examples:
    - I-B-M would be detected as acronym and it would return I.B.M as additional token
    - C.I.A would be detected as acronym and it would return C-I-A as additional token

    If no acronyms are detected for a token, an empty list is returned.
    """
    if not len(token):
        return []

    if token[0].isalpha():
        return _word_acronyms(token)
    elif token[0].isdigit():
        return _date_acronyms(token)
    return []


def tokenize_content(content):
    """
        We inherit the rules from the App Engine Search API
        when it comes to punctuation.

        We have a list of punctuation chars which break the
        content into tokens, and then some special cases where it
        makes sense. You can find the rules documented here:
        https://cloud.google.com/appengine/docs/standard/python/search#special-treatment
    """

    tokens = _tokenize_words(content)
    all_tokens = set(tokens)

    for token in tokens:
        acronyms_list = acronyms(token)
        if acronyms_list:
            all_tokens |= set(acronyms_list)

    return list(all_tokens)
