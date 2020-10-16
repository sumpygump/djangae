from .constants import (
    STOP_WORDS,
)

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


class DateTimeField(Field):
    pass


class NumberField(Field):
    def normalize_value(self, value):
        # FIXME: Validation?
        return int(value)

    def clean_token(self, value):
        return int(value)

    def tokenize_value(self, value):
        return [value]


class Document(object):
    # All documents have an 'id' property, if this is blank
    # when indexing, it will be populated with a generated one
    # This corresponds with the PK of the underlying DocumentRecord
    id = NumberField()

    @property
    def pk(self):
        return self.id

    def __init__(self, **kwargs):
        self._record = kwargs.get("_record", None)

        if self._record:
            self.id = self._record.pk
        else:
            self.id = kwargs.get("id")

        self._fields = {}

        klass = type(self)

        for attr_name in dir(klass):
            attr = getattr(klass, attr_name)

            if isinstance(attr, Field):
                attr.attname = attr_name
                self._fields[attr_name] = attr

                # We set the ID value above based on _record or 'id'
                # and we don't want to wipe that
                if attr_name == "id":
                    continue

                # Apply any field values passed into the init
                if attr_name in kwargs:
                    setattr(self, attr_name, kwargs[attr_name])
                else:
                    # Set default if there was no value
                    setattr(self, attr_name, attr.default)

    def get_fields(self):
        return self._fields

    def get_field(self, name):
        return self._fields[name]
