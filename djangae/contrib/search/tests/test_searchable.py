from djangae.test import TestCase

from .models import SearchableModel1


class SearchableTest(TestCase):
    def test_searching_models(self):
        i1 = SearchableModel1.objects.create(name="Luke")
        i2 = SearchableModel1.objects.create(name="Jimmy")  # noqa
        i3 = SearchableModel1.objects.create(name="Paolo")  # noqa
        i4 = SearchableModel1.objects.create(name="Purvi")  # noqa
        i5 = SearchableModel1.objects.create(name="Alton Powers")

        results = SearchableModel1.objects.search("luke")
        self.assertCountEqual(results, [i1])

        results = SearchableModel1.objects.search("powers")
        self.assertCountEqual(results, [i5])
