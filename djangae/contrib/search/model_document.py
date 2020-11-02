import copy
from functools import wraps

from django.core.exceptions import FieldDoesNotExist
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
        class Meta(getattr(cls, "Meta")):
            @property
            def all_fields(self):
                additional_fields = []

                # Gather fields added directly on the model document as
                # overrides, rather than added on the fields list
                for attr_name in dir(cls):
                    attr = getattr(cls, attr_name, None)
                    if isinstance(attr, search_fields.Field):
                        additional_fields.append(attr_name)

                return list(self.fields) + [
                    x for x in additional_fields if x not in self.fields
                ]

        return Meta()

    @classmethod
    def index(cls):
        meta = cls._meta()
        if meta:
            return Index(name=getattr(meta, "index", ""))
        else:
            return Index(name="")


def document_from_model_document(model, model_document):
    fields = model_document._meta().all_fields

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

        try:
            field_type = type(model._meta.get_field(field))
        except FieldDoesNotExist:
            # This would happen if we added a field override for
            # a model field that didn't exist
            continue

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


class SearchManagerBase(object):
    pass


def register(model, model_document):
    default_manager = type(getattr(model, "objects", Manager()))

    if isinstance(default_manager, SearchManagerBase):
        # Already patched!
        # FIXME: Use the registry instead?
        return

    document_class = document_from_model_document(model, model_document)

    def _do_search(query, **options):
        """
            Return a list of model instance_ids from the results
            of the specified query
        """

        index = model_document.index()
        documents = index.search(query, subclass=document_class, **options)
        return [x.instance_id for x in documents]

    class SearchQueryset(models.QuerySet):
        def search(self, query, **options):
            keys = _do_search(query, **options)
            return self.filter(pk__in=keys)

    class SearchManager(default_manager, SearchManagerBase):
        def get_queryset(self):
            qs = SearchQueryset(model, using=self._db)

            # Apply any filtering from any parent manager
            parent_qs = super().get_queryset()
            qs.query = parent_qs.query

            return qs

        def search(self, query, **options):
            keys = _do_search(query, **options)
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
                for f in model_document._meta().all_fields
            }

            attrs["instance_id"] = self.pk

            doc = document_class(**attrs)
            model_document.index().add(doc)
        return wrapped

    model.save = save_decorator(model.save)
