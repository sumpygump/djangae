from gcloudc.db import transaction

from .document import Document


class Index(object):

    def __init__(self, name):
        from .models import IndexStats  # Prevent import too early

        self.name = name
        self.index, created = IndexStats.objects.get_or_create(
            name=name
        )

    @property
    def id(self):
        return self.index.pk if self.index else None

    def add(self, document_or_documents):
        from .models import (  # Prevent import too early
            DocumentRecord,
            WordFieldIndex,
        )

        if isinstance(document_or_documents, Document):
            documents = [document_or_documents]
        else:
            documents = document_or_documents[:]

        for document in documents:
            # We go through the document fields, pull out the values that have been set
            # then we index them.

            field_data = {
                f: getattr(document, document.get_field(f).attname)
                for f in document.get_fields() if f != "id"
            }

            record = document._record

            created = False
            if record is None:
                # Generate a database representation of this Document use
                # the passed ID if there is one
                record, created = DocumentRecord.objects.get_or_create(
                    pk=document.id,
                    defaults={
                        "index_stats": self.index,
                        "data": field_data
                    }
                )
                document.id = record.id
                document._record = record

            if not created:
                record.data = field_data
                record.save()

            assert(document.id)  # This should be a thing by now

            for field_name, field in document.get_fields().items():
                if field_name == "id":
                    continue

                # Get the field value, use the default if it's not set
                value = getattr(document, field.attname, None)
                value = field.default if value is None else value
                value = field.normalize_value(value)

                # Tokenize the value, this will effectively mean lower-casing
                # removing punctuation etc. and returning a list of things
                # to index
                tokens = field.tokenize_value(value)

                if tokens is None:
                    # Nothing to index
                    continue

                for token in tokens:
                    token = field.clean_token(token)
                    if token is None:
                        continue

                    # FIXME: Update occurrances
                    with transaction.atomic():
                        try:
                            obj = WordFieldIndex.objects.get(
                                record_id=document.id,
                                word=token,
                                index_stats=self.index,
                                field_name=field.attname
                            )
                        except WordFieldIndex.DoesNotExist:
                            obj = WordFieldIndex.objects.create(
                                record_id=document.id,
                                index_stats=self.index,
                                word=token,
                                field_name=field.attname
                            )

                        record.refresh_from_db()
                        record.word_field_indexes.add(obj)
                        record.save()

    def remove(self, document_or_documents):
        pass

    def get(self, document_id):
        pass

    def search(self, query_string, limit=1000):
        from .query import build_document_queryset
        qs = build_document_queryset(query_string, self)[:limit]

        for record in qs:
            yield Document(_record=record, **record.data)
