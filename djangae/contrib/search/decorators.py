from functools import wraps

from django.db import models
from django.db.models import Manager

from djangae.contrib import search

from .index import Index


class ModelDocument(object):
    def __init__(self, model_class):
        self.model_class = model_class

    @classmethod
    def _meta(cls):
        return getattr(cls, "Meta", None)

    @classmethod
    def index(cls):
        meta = cls._meta()
        if meta:
            return Index(name=getattr(meta, "index", ""))
        else:
            return Index(name="")


def document_from_model_document(model_document, instance):
    fields = getattr(model_document._meta(), "fields", [])
    model = getattr(model_document._meta(), "model")

    mapping = {
        models.AutoField: search.NumberField,
        models.CharField: search.AtomField,
        models.TextField: search.TextField,
        models.DateTimeField: search.DateTimeField,
        models.IntegerField: search.NumberField,
        models.FloatField: search.AtomField,
        models.PositiveIntegerField: search.NumberField
    }

    pk_type = type(model._meta.pk)

    attrs = {
        "instance_id": mapping[pk_type]
    }

    for field in fields:
        # id is always stored as instance_id
        if field in ("pk", "id"):
            continue

        field_type = type(model._meta.get_field(field))
        attrs[field] = mapping[field_type]()

    Document = type(
        '%sDocument' % model.__name__,
        (search.Document,),
        attrs
    )

    # FIXME: This will fail with non-integer keys, need to
    # decide how to handle that (maybe another default _name field?)
    attrs = {
        f: model._meta.get_field(f).value_from_object(instance)
        for f in fields
    }

    return Document(**attrs)


def searchable(model_document):
    def decorator(klass):
        default_manager = type(getattr(klass, "objects", Manager()))

        class SearchManager(default_manager):
            def search(self, query):
                document_class = document_from_model_document(model_document)
                index = model_document.index()
                documents = [
                    x for x in index.search(query, subclass=document_class)
                ]
                keys = [x.instance_id for x in documents]
                return klass.objects.filter(pk__in=keys)

        klass.objects.__class__ = SearchManager

        def save_decorator(func):
            @wraps(func)
            def wrapped(self, *args, **kwargs):
                func(self, *args, **kwargs)
                doc = document_from_model_document(model_document, self)
                model_document.index().add(doc)
            return wrapped

        klass.save = save_decorator(klass.save)

        return klass

    return decorator
