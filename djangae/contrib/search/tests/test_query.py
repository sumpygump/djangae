from datetime import (
    datetime,
    timedelta,
)
from unittest import skip

from djangae.contrib.search import (
    Document,
    Index,
    fields,
)
from djangae.contrib.search.query import _tokenize_query_string
from djangae.test import TestCase


class CompanyDocument(Document):
    company_name = fields.TextField()


class FuzzyDocument(Document):
    company_name = fields.FuzzyTextField()


class QueryTests(TestCase):
    def test_tokenization_breaks_at_punctuation(self):
        q = "hi, there is a 100% chance this works [honest]"

        tokens = _tokenize_query_string(q)
        kinds = set(x[0] for x in tokens)
        tokens = [x[-1] for x in tokens]

        self.assertEqual(kinds, {"word"})  # All tokens should be recognised as "word" tokens
        self.assertEqual(tokens, ["hi", ",", "100", "%", "chance", "works", "[", "honest", "]"])

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

    def test_startswith_matching(self):
        index = Index(name="test")

        doc1 = CompanyDocument(company_name="Google")
        doc2 = CompanyDocument(company_name="Potato")
        doc3 = CompanyDocument(company_name="Facebook")
        doc4 = CompanyDocument(company_name="Potential Company")

        index.add(doc1)
        index.add(doc2)
        index.add(doc3)
        index.add(doc4)

        results = [x.company_name for x in index.search("goo", document_class=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Google"])

        results = [x.company_name for x in index.search("pot", document_class=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Potato", "Potential Company"])

        results = [x.company_name for x in index.search("pota", document_class=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Potato"])

    def test_number_field_querying(self):
        class Doc(Document):
            number = fields.NumberField()

        index = Index(name="test")

        doc1 = index.add(Doc(number=1))
        doc2 = index.add(Doc(number=2341920))

        results = [x for x in index.search("number:1", document_class=Doc)]

        # Should only return the exact match
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, doc1)

        results = [x for x in index.search("1", document_class=Doc)]

        # Should only return the exact match
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, doc1)

        results = [x for x in index.search("2341920", document_class=Doc)]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, doc2)

    def test_datefield_querying(self):
        class Doc(Document):
            datefield = fields.DateField()

        date = datetime(year=2020, month=1, day=1, hour=6, minute=15)
        tomorrow = date + timedelta(days=1)

        index = Index(name="test")
        index.add(Doc(datefield=date))
        index.add(Doc(datefield=tomorrow))

        results = [x for x in index.search("2020-01-01", document_class=Doc)]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].datefield, date)
