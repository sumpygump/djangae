from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index

from djangae.contrib.search import fields
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
