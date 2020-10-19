from djangae.contrib import search
from djangae.contrib.search import fields
from djangae.test import TestCase

from .models import SearchableModel1


class SearchableModelDocument(search.ModelDocument):
    class Meta:
        index = "index1"
        fields = (
            "name",
        )

    name = fields.FuzzyTextField()


search.register(SearchableModel1, SearchableModelDocument)


class SearchableTest(TestCase):
    def setUp(self):
        super().setUp()

        self.i1 = SearchableModel1.objects.create(name="Luke")
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
