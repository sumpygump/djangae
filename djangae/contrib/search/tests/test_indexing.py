
from djangae.test import TestCase

from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index
from djangae.contrib.search import fields

from djangae.contrib.search.models import WordFieldIndex


class QueryStringParseTests(TestCase):
    pass


class DocumentTests(TestCase):
    def test_get_fields(self):

        class DocOne(Document):
            pass

        class DocTwo(Document):
            text = fields.TextField()
            atom = fields.AtomField()

        doc = DocOne()
        self.assertEqual(list(doc.get_fields().keys()), ['id'])

        doc2 = DocTwo()
        self.assertEqual(3, len(doc2.get_fields()))


class IndexingTests(TestCase):
    def test_indexing_atom_fields(self):
        class Doc(Document):
            atom = fields.AtomField()

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
            text = fields.TextField()

        doc = Doc(text="This is a test. Cheese.")
        doc2 = Doc(text="This is also a test. Pickle.")

        index = Index(name="My Index")
        index.add(doc)
        index.add(doc2)

        # We should have some generated IDs now
        self.assertTrue(doc.id)
        self.assertTrue(doc2.id)

        results = [x for x in index.search("test", subclass=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("TEST", subclass=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("cheese OR pickle", subclass=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search('cheese OR text:pickle', subclass=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search('"cheese" OR pickle', subclass=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
          [doc.id, doc2.id],
          [x.id for x in results]
        )

    def test_removing_document(self):

        class Doc(Document):
            text = fields.TextField()

        i0 = Index(name="index1")
        i1 = Index(name="index2")

        d0 = i0.add(Doc(text="One"))

        # One field, one word
        self.assertEqual(
            WordFieldIndex.objects.count(),
            1
        )

        self.assertEqual(i0.document_count(), 1)
        self.assertEqual(i1.document_count(), 0)

        d1 = i0.add(Doc(text="Two"))

        # Two fields, one word each
        self.assertEqual(
            WordFieldIndex.objects.count(),
            2
        )

        self.assertEqual(i0.document_count(), 2)
        self.assertEqual(i1.document_count(), 0)

        d2 = i1.add(Doc(text="Three 3"))

        # Three fields, one word each except last which has 2
        self.assertEqual(
            WordFieldIndex.objects.count(),
            4
        )

        self.assertEqual(i0.document_count(), 2)
        self.assertEqual(i1.document_count(), 1)

        self.assertTrue(i0.remove(d0))
        self.assertFalse(i0.remove(d0))

        self.assertEqual(i0.document_count(), 1)
        self.assertEqual(i1.document_count(), 1)

        self.assertEqual(
            WordFieldIndex.objects.count(),
            3
        )

        self.assertFalse([x for x in i0.search("text:One")])

        self.assertTrue(i0.remove(d1))

        self.assertEqual(i0.document_count(), 0)
        self.assertEqual(i1.document_count(), 1)

        self.assertEqual(
            WordFieldIndex.objects.count(),
            2
        )

        self.assertFalse([x for x in i0.search("text:Two")])

        self.assertTrue(i1.remove(d2))

        self.assertEqual(i0.document_count(), 0)
        self.assertEqual(i1.document_count(), 0)

        self.assertEqual(
            WordFieldIndex.objects.count(),
            0
        )

        self.assertFalse([x for x in i1.search("text:Three")])
        self.assertFalse([x for x in i1.search("text:3")])

    def test_pipe_not_indexed(self):
        """
            The | symbols is used for WordFieldIndex key generation
            so shouldn't be indexed... ever!
        """

        class Doc(Document):
            name = fields.TextField()

        index = Index(name="test")
        index.add(Doc(name="|| Pipes"))

        self.assertEqual(index.document_count(), 1)
        self.assertEqual(WordFieldIndex.objects.count(), 1)  # Just "pipes"
