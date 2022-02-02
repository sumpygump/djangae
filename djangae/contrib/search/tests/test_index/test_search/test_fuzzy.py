from unittest import skip

from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
from djangae.test import TestCase


class FuzzyDocument(Document):
    company_name = fields.FuzzyTextField()


class SearchFuzzyTests(TestCase):

    @skip("Implement stemming and fix this test")
    def test_fuzzy_matching(self):
        index = Index(name="test")

        doc1 = FuzzyDocument(company_name="Google")
        doc2 = FuzzyDocument(company_name="Potato")
        doc3 = FuzzyDocument(company_name="Facebook")
        doc4 = FuzzyDocument(company_name="Potential Company")

        index.add(doc1)
        index.add(doc2)
        index.add(doc3)
        index.add(doc4)

        results = [x.company_name for x in index.search("goo", document_class=FuzzyDocument)]
        self.assertCountEqual(results, ["Google"])

        results = [x.company_name for x in index.search("pot", document_class=FuzzyDocument)]
        self.assertCountEqual(results, ["Potato", "Potential Company"])

        results = [x.company_name for x in index.search("pota", document_class=FuzzyDocument)]
        self.assertCountEqual(results, ["Potato"])
