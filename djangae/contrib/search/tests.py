

from djangae.test import TestCase
from djangae.contrib import search

from .document import Document
from .index import Index


class QueryStringParseTests(TestCase):
    pass


class DocumentTests(TestCase):
    def test_get_fields(self):

        class DocOne(Document):
            pass

        class DocTwo(Document):
            text = search.TextField()
            atom = search.AtomField()

        doc = DocOne()
        self.assertEqual(doc.get_fields(), {})

        doc2 = DocTwo()
        self.assertEqual(2, len(doc2.get_fields()))


class IndexingTests(TestCase):
    def test_indexing_atom_fields(self):
        class Doc(Document):
            atom = search.AtomField()

        doc1 = Doc(atom="This is a test")
        doc2 = Doc(atom="This is also a test")
        doc3 = Doc(atom="This")

        index = Index(name="MyIndex")
        index.add(doc1)
        index.add(doc2)

        # Exact match, or exact field match should return doc1
        self.assertTrue(doc1 in index.search('atom:"This is a test"'))
        self.assertFalse(doc2 in index.search('atom:"This is a test"'))
        self.assertTrue(doc1 in index.search('"This is a test"'))

        # Partial match should only return exact atom matches
        self.assertTrue(doc3 in index.search('This'))
        self.assertFalse(doc1 in index.search('This'))
        self.assertFalse(doc2 in index.search('This'))

    def test_indexing_text_fields(self):
        class Doc(Document):
            text = search.TextField()

        doc = Doc(text="This is a test. Cheese.")
        doc2 = Doc(text="This is also a test. Pickle.")

        index = Index(name="My Index")
        index.add(doc)
        index.add(doc2)

        # We should have some generated IDs now
        self.assertTrue(doc.id)
        self.assertTrue(doc2.id)

        results = [x for x in index.search("test")]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("TEST")]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("cheese OR pickle")]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search('cheese OR text:pickle')]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search('"cheese" OR pickle')]

        # Both documents should have come back
        self.assertCountEqual(
          [doc.id, doc2.id],
          [x.id for x in results]
        )
