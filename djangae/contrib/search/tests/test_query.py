from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
from djangae.contrib.search import query
from djangae.test import TestCase


class SearchRankingTests(TestCase):

    def test_ordered_by_rank(self):
        class Doc(Document):
            text = fields.TextField()
            rank = fields.NumberField()

        index = Index(name="test")
        doc1 = index.add(Doc(text="test", rank=100))
        doc2 = index.add(Doc(text="test", rank=50))
        doc3 = index.add(Doc(text="test", rank=150))

        results = list(index.search("test", Doc, order_by="rank"))

        self.assertEqual(results[0].id, doc2)
        self.assertEqual(results[1].id, doc1)
        self.assertEqual(results[2].id, doc3)

    def test_default_ordering_is_sensible(self):
        """
            Ranking should be as follows:

             - Stopwords match weakest
             - When startswith matching is enabled, closer matches to the
               searched term will be stronger
        """

        class Doc(Document):
            text = fields.TextField()

            def __repr__(self):
                return "<Document %s>" % self.text

        index = Index(name="test")

        doc1 = Doc(text="all about you")  # All stopwords
        doc2 = Doc(text="ready to rumble")  # 2 stopwords
        doc3 = Doc(text="live forever")  # no stopwords
        doc4 = Doc(text="live and let die")  # 1 stop word
        index.add([doc1, doc2, doc3, doc4])

        results = list(index.search("live to forever", Doc, match_all=False))

        expected_order = [
            doc3,  # live forever
            doc4,  # live
            doc2,  # to
        ]

        self.assertEqual(results, expected_order)

        results = list(index.search("all about forever and", Doc, match_all=False))

        expected_order = [
            doc3,  # live forever
            doc1,  # all about
            doc4,  # and
        ]

        self.assertEqual(results, expected_order)


class CompareTokensMatchAllTests(TestCase):
    def test_search_single_token_single_found(self):
        res = query._compare_tokens(
            set({'goo'}),
            set({'google'}),
            match_all=True,
            use_startswith=True
        )
        self.assertTrue(res)

    def test_search_single_token_multi_found(self):
        res = query._compare_tokens(
            set({'goo'}),
            set({'google', 'llc'}),
            match_all=True,
            use_startswith=True
        )
        self.assertTrue(res)

    def test_search_multiple_tokens_multiple_found_startswith_match(self):
        res = query._compare_tokens(
            set({'goo', 'llc'}),
            set({'google', 'llc'}),
            match_all=True,
            use_startswith=True
        )
        self.assertTrue(res)

    def test_search_multiple_tokens__partial_single_found_startswith_no_match(self):
        """Only one of the two sarched terms is found, but match all would require both
        both to be there."""
        res = query._compare_tokens(
            set({'goo', 'llc'}),
            set({'llc'}),
            match_all=True,
            use_startswith=True
        )
        self.assertFalse(res)

    def test_search_multiple_tokens_single_found_startswith_no_match(self):
        """None of the searched terms are found, it should return `False`."""
        res = query._compare_tokens(
            set({'aaa', 'bbb'}),
            set({'llc'}),
            match_all=True,
            use_startswith=True
        )
        self.assertFalse(res)


class CompareTokensNotMatchAllTests(TestCase):
    def test_match_all_false_always_returns_a_compare(self):
        """When match_all=False we always compare."""
        res = query._compare_tokens(
            set({'goo', 'llc'}),
            set({'llc'}),
            match_all=False,
            use_startswith=True
        )
        self.assertTrue(res)

        res = query._compare_tokens(
            set({'goo'}),
            set({'google'}),
            match_all=False,
            use_startswith=True
        )
        self.assertTrue(res)

        res = query._compare_tokens(
            set({'goo'}),
            set({'google', 'llc'}),
            match_all=False,
            use_startswith=True
        )
        self.assertTrue(res)


class TokenizeQueryStringTests(TestCase):

    def test_word_with_lodash(self):
        q_string = 'query_string'
        expected_query = [[('word', None, 'querystring'), ('word', None, 'query_string')]]
        query_token = expected_query[0]

        res = query._tokenize_query_string(q_string, False)

        res_kind = [r[0] for r in query_token]
        res_field = [r[1] for r in query_token]
        res_content = [r[2] for r in query_token]
        first_kind, first_field, first_content = query_token[0]
        second_kind, second_field, second_content = query_token[1]

        self.assertEqual(len(res[0]), len(query_token))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

        self.assertTrue(second_kind in res_kind)
        self.assertTrue(second_field in res_field)
        self.assertTrue(second_content in res_content)

    def test_query_with_single_symbol(self):
        q_string = 'query    ,'
        expected_query = [[('word', None, 'query')]]
        query_token = expected_query[0]

        res = query._tokenize_query_string(q_string, False)

        res_kind = [r[0] for r in query_token]
        res_field = [r[1] for r in query_token]
        res_content = [r[2] for r in query_token]
        first_kind, first_field, first_content = query_token[0]

        self.assertEqual(len(res[0]), len(query_token))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

    def test_symbol_with_word(self):
        q_string = 'query    ,something'
        expected_query = [[('word', None, 'query'), ('word', None, ',something'), ('word', None, 'something')]]
        query_token = expected_query[0]

        res = query._tokenize_query_string(q_string, False)

        res_kind = [r[0] for r in query_token]
        res_field = [r[1] for r in query_token]
        res_content = [r[2] for r in query_token]
        first_kind, first_field, first_content = query_token[0]
        second_kind, second_field, second_content = query_token[1]

        self.assertEqual(len(res[0]), len(query_token))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

        self.assertTrue(second_kind in res_kind)
        self.assertTrue(second_field in res_field)
        self.assertTrue(second_content in res_content)

    def test_partial_exact(self):
        q_string = 'query    "something exact"'
        expected_query = [[('word', None, 'query'), ('exact', None, 'something exact')]]
        query_token = expected_query[0]

        res = query._tokenize_query_string(q_string, False)

        res_kind = [r[0] for r in query_token]
        res_field = [r[1] for r in query_token]
        res_content = [r[2] for r in query_token]
        first_kind, first_field, first_content = query_token[0]
        second_kind, second_field, second_content = query_token[1]

        self.assertEqual(len(res[0]), len(query_token))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

        self.assertTrue(second_kind in res_kind)
        self.assertTrue(second_field in res_field)
        self.assertTrue(second_content in res_content)

    def test_exact_full(self):
        q_string = '"something exact"'
        expected_query = [[('exact', None, 'something exact')]]
        query_token = expected_query[0]

        res = query._tokenize_query_string(q_string, False)

        res_kind = [r[0] for r in query_token]
        res_field = [r[1] for r in query_token]
        res_content = [r[2] for r in query_token]
        first_kind, first_field, first_content = query_token[0]

        self.assertEqual(len(res[0]), len(query_token))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

    def test_or_query(self):
        q_string = '"something exact" or something else'
        expected_query = [[('exact', None, 'something exact')], [('word', None, 'something'), ('word', None, 'else')]]
        query_token_0 = expected_query[0]
        query_token_1 = expected_query[1]

        res = query._tokenize_query_string(q_string, False)

        # check exact part
        res_kind = [r[0] for r in query_token_0]
        res_field = [r[1] for r in query_token_0]
        res_content = [r[2] for r in query_token_0]
        first_kind, first_field, first_content = query_token_0[0]

        self.assertEqual(len(res), len(expected_query))
        self.assertEqual(len(res[0]), len(query_token_0))
        self.assertEqual(len(res[1]), len(query_token_1))

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

        # check or part
        res_kind = [r[0] for r in query_token_1]
        res_field = [r[1] for r in query_token_1]
        res_content = [r[2] for r in query_token_1]
        first_kind, first_field, first_content = query_token_1[0]
        second_kind, second_field, second_content = query_token_1[1]

        self.assertTrue(first_kind in res_kind)
        self.assertTrue(first_field in res_field)
        self.assertTrue(first_content in res_content)

        self.assertTrue(second_kind in res_kind)
        self.assertTrue(second_field in res_field)
        self.assertTrue(second_content in res_content)
