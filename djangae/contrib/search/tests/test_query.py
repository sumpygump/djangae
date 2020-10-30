from djangae.test import TestCase
from djangae.contrib.search.query import _tokenize_query_string

from djangae.contrib.search import Document
from djangae.contrib.search import Index
from djangae.contrib.search import fields


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

        self.assertEqual(kinds, {"word"})  # All tokens should be recognised as tokens
        self.assertEqual(tokens, ["hi", ",", "100", "%", "chance", "works", "[", "honest", "]"])

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

        results = [x.company_name for x in index.search("goo", subclass=FuzzyDocument)]
        self.assertCountEqual(results, ["Google"])

        results = [x.company_name for x in index.search("pot", subclass=FuzzyDocument)]
        self.assertCountEqual(results, ["Potato", "Potential Company"])

        results = [x.company_name for x in index.search("pota", subclass=FuzzyDocument)]
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

        results = [x.company_name for x in index.search("goo", subclass=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Google"])

        results = [x.company_name for x in index.search("pot", subclass=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Potato", "Potential Company"])

        results = [x.company_name for x in index.search("pota", subclass=CompanyDocument, use_startswith=True)]
        self.assertCountEqual(results, ["Potato"])
