from djangae.contrib import search
from djangae.contrib.search import fields
from djangae.contrib.search.model_document import document_from_model_document
from djangae.contrib.search.models import TokenFieldIndex
from djangae.test import TestCase

from .models import (
    SearchableModel1,
    SearchableModel2,
)


class SearchableModelDocument(search.ModelDocument):
    class Meta:
        index = "index1"
        fields = (
            "name",
        )

    other_thing = fields.NumberField()


class CharFieldPK(search.ModelDocument):
    class Meta:
        fields = (
            "sid",
        )


class SearchableTest(TestCase):
    def setUp(self):
        # Ensure that the model has been registered
        search.register(SearchableModel1, SearchableModelDocument)
        search.register(SearchableModel2, CharFieldPK)

        super().setUp()

        self.i1 = SearchableModel1.objects.create(id=1, name="Luke")
        self.i2 = SearchableModel1.objects.create(name="Jimmy")  # noqa
        self.i3 = SearchableModel1.objects.create(name="Paolo")  # noqa
        self.i4 = SearchableModel1.objects.create(name="Purvi")  # noqa
        self.i5 = SearchableModel1.objects.create(name="Alton Powers")
        self.instances = [self.i1, self.i2, self.i3, self.i4, self.i5]

    def test_searching_models(self):
        results = SearchableModel1.objects.search("luke")
        self.assertCountEqual(results, [self.i1])

        results = SearchableModel1.objects.search("powers")
        self.assertCountEqual(results, [self.i5])

    def test_queryset_filtering(self):
        qs = SearchableModel1.objects.filter(
            pk__in=[self.i1.pk, self.i2.pk]
        ).search("luke")

        self.assertCountEqual(qs, [self.i1])

    def test_field_override(self):
        document = document_from_model_document(SearchableModel1, SearchableModelDocument)

        # The name field should be overridden, it would default to
        self.assertEqual(type(document.other_thing), fields.NumberField)

    def test_charfield_pk(self):
        i1 = SearchableModel2.objects.create(sid="test")
        i2 = SearchableModel2.objects.create(sid=1)  # Intentional integer
        i2.refresh_from_db()

        results = SearchableModel2.objects.search("test")
        self.assertCountEqual([i1], results)

        results = SearchableModel2.objects.search("sid:1")
        self.assertCountEqual([i2], results)

    def test_deletion(self):
        results = SearchableModel1.objects.search("jimmy")
        self.assertTrue([x for x in results])

        count = TokenFieldIndex.objects.count()
        idx = SearchableModelDocument.index()

        doc_count = idx.document_count()
        self.i2.delete()
        self.assertEqual(idx.document_count(), doc_count - 1)

        new_count = TokenFieldIndex.objects.count()
        self.assertTrue(new_count < count)

        results = SearchableModel1.objects.search("jimmy")
        self.assertFalse([x for x in results])

    def test_update(self):
        results = SearchableModel1.objects.search("jimmy")
        self.assertTrue([x for x in results])

        self.i2.name = "bob"
        self.i2.save()

        results = SearchableModel1.objects.search("jimmy")
        self.assertFalse([x for x in results])

        results = SearchableModel1.objects.search("bob")
        self.assertTrue([x for x in results])
