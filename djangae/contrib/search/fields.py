from .constants import STOP_WORDS
from .tokens import tokenize_content
from . import indexers as search_indexers


class Field(object):
    def __init__(self, default=None, null=True):
        self.default = default
        self.null = null

    def normalize_value(self, value):
        # Default behaviour is to lower-case, remove punctuation
        # and then remove stop words

        if value is None:
            return None

        # Lower-case everything by default
        value = value.lower()

        # Normalize whitespace
        return " ".join(value.split())

    def tokenize_value(self, value):
        """
            Given a value set on a document, this
            returns a list of tokens that are indexed
        """
        if value is None:
            return value

        return tokenize_content(value)

    def clean_token(self, token):
        """
            Called on each token, if the token should be discarded,
            return None.
        """

        token = token.strip()  # Just in case
        if token in STOP_WORDS:
            return None  # Ignore stop words

        # Remove + signs, unless they are trailing
        if "+" in token:
            plus_count = 0
            while token[-1] == "+":
                token = token[:-1]
                plus_count += 1

            token = token.replace("+", "") + ("+" * plus_count)

        if "#" in token:
            # Replace hashes unless it's a music note or programming language
            if len(token) > 2 or token[-1] != "#" or token[0] not in "abcdefgjx":
                token = token.replace("#", "")

        # Remove leading or trailing periods. In acronyms it's fine FIXME: handle "abs.dasd"
        token = token.strip(".")

        return token


class AtomField(Field):
    pass


class TextField(Field):
    pass


class FuzzyTextField(TextField):
    DEFAULT_INDEXERS = (
        search_indexers.stemming,
    )

    def __init__(self, default=None, null=True, indexers=None, min_index_length=3, **kwargs):
        """
            indexers: list of indexers to apply to the value for indexing
            min_index_length: resulting tokens less than this length will be ignored
        """

        self.indexers = indexers or FuzzyTextField.DEFAULT_INDEXERS
        self.options = {
            "min_index_length": min_index_length
        }

        super().__init__(default=default, null=null, **kwargs)

    def tokenize_value(self, value):
        result = []
        tokens = super().tokenize_value(value)
        for token in tokens:
            for indexer in self.indexers:
                result.extend(indexer(token, **self.options))

        return result


class DateTimeField(Field):
    pass


class NumberField(Field):
    def normalize_value(self, value):
        # FIXME: Validation?
        return int(value)

    def clean_token(self, value):
        return str(int(value))

    def tokenize_value(self, value):
        return [value]
