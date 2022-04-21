from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
from djangae.test import TestCase


class CompanyDocument(Document):
    company_name = fields.TextField()
    company_type = fields.TextField()


class FuzzyDocument(Document):
    company_name = fields.FuzzyTextField()


class DocNumber(Document):
    number = fields.NumberField()


class DocumentText(Document):
    text = fields.TextField()


class SearchMatchAllFalseWordsTests(TestCase):
    """Test case for search function with `use_startswith=True` and `match_all=False`."""
    def setUp(self):
        super().setUp()
        self.index = Index(name="test")

        doc1 = CompanyDocument(company_name="Google", company_type="LLC")
        doc2 = CompanyDocument(company_name="Potato", company_type="Ltd.")
        doc3 = CompanyDocument(company_name="Facebook", company_type="Inc.")
        doc4 = CompanyDocument(company_name="Awesome", company_type="LLC")
        doc5 = CompanyDocument(company_name="Potential Company", company_type="Ltd.")

        self.index.add(doc1)
        self.index.add(doc2)
        self.index.add(doc3)
        self.index.add(doc4)
        self.index.add(doc5)

    def test_startswith_matching_one_result(self):
        search_results = self.index.search(
            "pota",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [x.company_name for x in search_results]
        self.assertCountEqual(results, ["Potato"])
        self.assertTrue("Potato" in results)

    def test_startswith_matching_more_results(self):
        search_results = self.index.search(
            "pot",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [x.company_name for x in search_results]

        self.assertCountEqual(results, ["Potato", "Potential Company"])
        self.assertTrue("Potato" in results)
        self.assertTrue("Potential Company" in results)

    def test_startswith_matching_no_results(self):
        search_results = self.index.search(
            "nores",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [x.company_name for x in search_results]
        self.assertCountEqual(results, [])

    def test_startswith_multiple_tokens_single_result(self):

        search_results = self.index.search(
            "goo aa",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [(x.company_name, x.company_type) for x in search_results]

        self.assertCountEqual(results, [("Google", "LLC")])
        self.assertTrue("Google" in [x[0] for x in results])
        self.assertTrue("LLC" in [x[1] for x in results])

    def test_startswith_multiple_tokens_multi_results(self):
        search_results = self.index.search(
            "pot ltd",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [(x.company_name, x.company_type) for x in search_results]
        company_names = [x[0] for x in results]
        company_types = [x[1] for x in results]

        self.assertCountEqual(results, [("Potato", "Ltd."), ("Potential Company", "Ltd.")])
        self.assertTrue("Potato" in company_names)
        self.assertTrue("Potential Company" in company_names)
        self.assertTrue("Ltd." in company_types)

    def test_startswith_multiple_tokens_no_results(self):
        search_results = self.index.search(
            "no res",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=False,
        )

        results = [(x.company_name, x.company_type) for x in search_results]

        self.assertEqual(len(results), 0)

    def test_trailing_period(self):

        index = Index(name="test-2")
        index.add(DocumentText(text="My company ltd."))
        index.add(DocumentText(text="Company co."))

        results = list(index.search("co", DocumentText, match_all=False))
        self.assertEqual(len(results), 1)

        results = list(index.search("co.", DocumentText, match_all=False))
        self.assertEqual(len(results), 1)

        results = list(index.search("ltd", DocumentText, match_all=False))
        self.assertEqual(len(results), 1)

        results = list(index.search("ltd.", DocumentText, match_all=False))
        self.assertEqual(len(results), 1)

    def test_should_default_to_or_flag(self):
        index = Index(name="test")
        index.add(DocumentText(text="test string one"))
        index.add(DocumentText(text="test string two"))

        # Should return both as we're defaulting to OR behaviour
        results = list(index.search("string one", DocumentText, match_all=False))
        self.assertEqual(len(results), 2)

    def test_or_queries(self):
        index = Index(name="test")
        index.add(DocumentText(text="test string one"))
        index.add(DocumentText(text="test string two"))

        results = list(index.search("one OR two", DocumentText, match_all=False))
        self.assertEqual(len(results), 2)


class SearchMatchAllFalseAcronymsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.index = Index(name="test-acronyms")
        self.doc1 = self.index.add(DocumentText(text="a.b.c"))
        self.doc2 = self.index.add(DocumentText(text="1-2-3"))
        self.index.add(DocumentText(text="do-re-mi"))

    def test_acronyms_search_with_no_symbols(self):
        results = list(self.index.search("abc", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_partial_search_with_no_symbols(self):
        results = list(self.index.search("bc", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 0)

    def test_acronyms_search_with_no_symbols_startswith(self):

        results = list(self.index.search("abc", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_partial_search_with_no_symbols_startswith(self):

        results = list(self.index.search("bc", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 0)

    def test_acronyms_with_symbols(self):
        results = list(self.index.search("a.b.c", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("b.c", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("a-b-c", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("2-3", DocumentText, use_startswith=False, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc2)

    def test_acronyms_with_symbols_startswith(self):
        results = list(self.index.search("a.b.c", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("b.c", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("a-b-c", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("2-3", DocumentText, use_startswith=True, match_all=False))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc2)


class SearchMatchAllTrueWordsTests(TestCase):
    """Test case for search function with `use_startswith=True` and `match_all=True`."""
    def setUp(self):
        super().setUp()
        self.index = Index(name="test")

        doc1 = CompanyDocument(company_name="Google", company_type="LLC")
        doc2 = CompanyDocument(company_name="Potato", company_type="Ltd.")
        doc3 = CompanyDocument(company_name="Facebook", company_type="Inc.")
        doc4 = CompanyDocument(company_name="Awesome", company_type="LLC")
        doc5 = CompanyDocument(company_name="Potential Company", company_type="Ltd.")

        self.index.add(doc1)
        self.index.add(doc2)
        self.index.add(doc3)
        self.index.add(doc4)
        self.index.add(doc5)

    def test_startswith_matching_one_result(self):
        search_results = self.index.search(
            "pota",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [x.company_name for x in search_results]
        self.assertCountEqual(results, ["Potato"])
        self.assertTrue("Potato" in results)

    def test_startswith_matching_more_results(self):
        search_results = self.index.search(
            "pot",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [x.company_name for x in search_results]

        self.assertCountEqual(results, ["Potato", "Potential Company"])
        self.assertTrue("Potato" in results)
        self.assertTrue("Potential Company" in results)

    def test_startswith_matching_no_results(self):
        search_results = self.index.search(
            "nores",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [x.company_name for x in search_results]
        self.assertCountEqual(results, [])

    def test_startswith_multiple_tokens_single_result(self):

        search_results = self.index.search(
            "goo llc",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [(x.company_name, x.company_type) for x in search_results]

        self.assertCountEqual(results, [("Google", "LLC")])
        self.assertTrue("Google" in [x[0] for x in results])
        self.assertTrue("LLC" in [x[1] for x in results])

    def test_startswith_multiple_tokens_multi_results(self):
        search_results = self.index.search(
            "pot ltd",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [(x.company_name, x.company_type) for x in search_results]
        company_names = [x[0] for x in results]
        company_types = [x[1] for x in results]

        self.assertCountEqual(results, [("Potato", "Ltd."), ("Potential Company", "Ltd.")])
        self.assertTrue("Potato" in company_names)
        self.assertTrue("Potential Company" in company_names)
        self.assertTrue("Ltd." in company_types)

    def test_startswith_multiple_tokens_no_results(self):
        search_results = self.index.search(
            "no res",
            document_class=CompanyDocument,
            use_startswith=True,
            match_all=True,
        )

        results = [(x.company_name, x.company_type) for x in search_results]

        self.assertEqual(len(results), 0)

    def test_trailing_period(self):
        index = Index(name="test-2")
        index.add(DocumentText(text="My company ltd."))
        index.add(DocumentText(text="Company co."))

        results = list(index.search("co", DocumentText, match_all=True))
        self.assertEqual(len(results), 1)

        results = list(index.search("co.", DocumentText, match_all=True))
        self.assertEqual(len(results), 1)

        results = list(index.search("ltd", DocumentText, match_all=True))
        self.assertEqual(len(results), 1)

        results = list(index.search("ltd.", DocumentText, match_all=True))
        self.assertEqual(len(results), 1)

        results = list(index.search("ltd .", DocumentText, match_all=True))
        self.assertEqual(len(results), 1)

    def test_or_queries(self):
        index = Index(name="test")
        index.add(DocumentText(text="test string one"))
        index.add(DocumentText(text="test string two"))

        results = list(index.search("one OR two", DocumentText, match_all=True))
        self.assertEqual(len(results), 2)


class SearchMatchAllTrueAcronymsTests(TestCase):
    def setUp(self):
        super().setUp()
        self.index = Index(name="test-acronyms")
        self.doc1 = self.index.add(DocumentText(text="a.b.c"))
        self.doc2 = self.index.add(DocumentText(text="1-2-3"))
        self.index.add(DocumentText(text="do-re-mi"))

    def test_acronyms_search_with_no_symbols(self):
        results = list(self.index.search("abc", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_partial_search_with_no_symbols(self):
        results = list(self.index.search("bc", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 0)

    def test_acronyms_search_with_no_symbols_startswith(self):

        results = list(self.index.search("abc", DocumentText, use_startswith=True, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_partial_search_with_no_symbols_startswith(self):

        results = list(self.index.search("bc", DocumentText, use_startswith=True, match_all=True))
        self.assertEqual(len(results), 0)

    def test_acronyms_with_symbols(self):
        results = list(self.index.search("a.b.c", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("a-b-c", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_with_symbols_startswith(self):
        results = list(self.index.search("a.b.c", DocumentText, use_startswith=True, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

        results = list(self.index.search("a-b-c", DocumentText, use_startswith=True, match_all=True))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, self.doc1)

    def test_acronyms_partial_match_with_symbols_startswith(self):
        results = list(self.index.search("b.c", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 0)

        results = list(self.index.search("2-3", DocumentText, use_startswith=False, match_all=True))
        self.assertEqual(len(results), 0)
