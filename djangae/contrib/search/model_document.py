import copy
from functools import wraps

from django.db import models
from django.db.models import Manager

from djangae.contrib import search
from djangae.contrib.search import fields as search_fields

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
        models.AutoField: search_fields.NumberField,
        models.CharField: search_fields.TextField,
        models.TextField: search_fields.TextField,
        models.DateTimeField: search_fields.DateTimeField,
        models.IntegerField: search_fields.NumberField,
        models.FloatField: search_fields.NumberField,
        models.PositiveIntegerField: search_fields.NumberField
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

        # First, do we have an override on the model document itself?
        if hasattr(model_document, field):
            # We copy, so we don't mess with the class version of this
            attrs[field] = copy.deepcopy(getattr(model_document, field))
        else:
            attrs[field] = mapping[field_type]()

    Document = type(
        '%sDocument' % model.__name__,
        (search.Document,),
        attrs
    )

    return Document


_registry = {}


def register(model, model_document):
    default_manager = type(getattr(model, "objects", Manager()))
    document_class = document_from_model_document(model, model_document)

    def _do_search(query):
        """
            Return a list of model instance_ids from the results
            of the specified query
        """

        index = model_document.index()
        documents = index.search(query, subclass=document_class)
        return [x.instance_id for x in documents]

    class SearchQueryset(models.QuerySet):
        def search(self, query):
            keys = _do_search(query)
            return self.filter(pk__in=keys)

    class SearchManager(default_manager):
        def get_queryset(self):
            qs = SearchQueryset(model, using=self._db)

            # Apply any filtering from any parent manager
            parent_qs = super().get_queryset()
            qs.query = parent_qs.query

            return qs

        def search(self, query):
            keys = _do_search(query)
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
