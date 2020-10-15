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


def document_from_model_document(model, model_document):
    fields = getattr(model_document._meta(), "fields", [])

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
        "instance_id": mapping[pk_type]()
    }

    fields = list(fields) + ["instance_id"]

    for field in fields:
        # id is always stored as instance_id
        if field == "instance_id":
            continue

        field_type = type(model._meta.get_field(field))
        attrs[field] = mapping[field_type]()

    Document = type(
        '%sDocument' % model.__name__,
        (search.Document,),
        attrs
    )

    return Document


def register(model, model_document):
    default_manager = type(getattr(model, "objects", Manager()))
    document_class = document_from_model_document(model, model_document)

    class SearchManager(default_manager):
        def search(self, query):

            index = model_document.index()
            documents = [
                x for x in index.search(query, subclass=document_class)
            ]
            keys = [x.instance_id for x in documents]
            return model.objects.filter(pk__in=keys)

    # FIXME: Is this safe? I feel like it should be but 'objects' is
    # a ManagerDescriptor so this might not be doing what I think it
    # is.
    model.objects.__class__ = SearchManager

    def save_decorator(func):
        @wraps(func)
        def wrapped(self, *args, **kwargs):
            func(self, *args, **kwargs)

            attrs = {
                f: model._meta.get_field(f).value_from_object(self)
                for f in getattr(model_document._meta(), "fields", [])
            }

            attrs["instance_id"] = self.pk
            doc = document_class(**attrs)
            model_document.index().add(doc)
        return wrapped

    model.save = save_decorator(model.save)
