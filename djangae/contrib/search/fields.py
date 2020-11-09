import logging
from datetime import datetime

from django.utils import dateparse

from . import indexers as search_indexers
from .constants import STOP_WORDS
from .tokens import tokenize_content


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

        tokens, new_tokens = tokenize_content(value)
        tokens.extend(new_tokens)
        return tokens

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

        return token

    def convert_from_index(self, value):
        """
            Convert a value returned from the index (these values)
            are stored in JSON format, so value will be a string, number, bool
            or None
        """
        return value


class AtomField(Field):
    pass


class TextField(Field):
    def normalize_value(self, value):
        if value is not None:
            value = str(value)

        return super().normalize_value(value)


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


class DateField(Field):
    def normalize_value(self, value):
        if value is None:
            return value

        if isinstance(value, str):
            return dateparse.parse_datetime(value)

        assert(isinstance(value, datetime))

        return value

    def tokenize_value(self, value):
        if value is None:
            return value

        # FIXME: It would be great to make this a datetime field
        # and handle times but that gets tricky quickly when you
        # consider timezones...
        return [
            value.strftime("%Y-%m-%d"),
        ]

    def convert_from_index(self, value):
        if value is None:
            return value

        try:
            return dateparse.parse_datetime(value)
        except ValueError:
            logging.warning("Unable to convert datetime back")
            return None


class NumberField(Field):
    def normalize_value(self, value):
        # FIXME: Validation?
        return int(value)

    def clean_token(self, value):
        return str(int(value))

    def tokenize_value(self, value):
        return [value]
