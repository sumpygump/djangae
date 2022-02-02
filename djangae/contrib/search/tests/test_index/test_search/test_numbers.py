from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
from djangae.test import TestCase


class DocumentNumber(Document):
    number = fields.NumberField()


class SearchMatchAllTrueNumbersTests(TestCase):
    """Test class to perform a search using match_all flag set to `True`."""
    def setUp(self):
        super().setUp()
        self.index = Index(name="test")
        self.doc1 = self.index.add(DocumentNumber(number=1))
        self.doc2 = self.index.add(DocumentNumber(number=2341920))

    def test_number_keyword_specified_exact_match(self):
        search_results = self.index.search(
            "number:1",
            document_class=DocumentNumber,
            match_all=True
        )

        results = [x for x in search_results]

        # Should only return the exact match
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_without_number_keyword_specified_exact_match(self):
        search_results = self.index.search(
            "1",
            document_class=DocumentNumber,
            match_all=True
        )
        results = [x for x in search_results]

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        search_results = self.index.search(
            "2341920",
            document_class=DocumentNumber,
            match_all=True
        )

        results = [x for x in search_results]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc2)
