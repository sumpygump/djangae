from datetime import (
    datetime,
    timedelta,
)
from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
from djangae.test import TestCase


class DocumentDate(Document):
    datefield = fields.DateField()


class SearchDatesTests(TestCase):
    """Test class to perform a search using match_all flag set to `True`."""
    def setUp(self):
        super().setUp()
        self.index = Index(name="test")
        self.date = datetime(year=2020, month=1, day=1, hour=6, minute=15)
        self.tomorrow = self.date + timedelta(days=1)

        self.index.add(DocumentDate(datefield=self.date))
        self.index.add(DocumentDate(datefield=self.tomorrow))

    def test_datefield_querying_match_all(self):

        results = [x for x in self.index.search("2020-01-01", document_class=DocumentDate, match_all=True)]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].datefield, self.date)

    def test_datefield_querying_match_all_false(self):
        results = [x for x in self.index.search("2020-01-01", document_class=DocumentDate, match_all=False)]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].datefield, self.date)

    def test_datefield_querying_partial_match_no_result(self):
        results_not_match_all = [x for x in self.index.search("2020-01", document_class=DocumentDate, match_all=False)]
        results_match_all = [x for x in self.index.search("2020-01", document_class=DocumentDate, match_all=True)]
        self.assertEqual(len(results_match_all), 0)
        self.assertEqual(len(results_not_match_all), 0)
