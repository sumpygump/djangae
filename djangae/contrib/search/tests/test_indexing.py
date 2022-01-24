from unittest import skip, mock

from djangae.contrib.search import fields
from djangae.contrib.search.document import Document
from djangae.contrib.search.index import Index
from djangae.contrib.search.models import TokenFieldIndex
from djangae.contrib.search.tokens import tokenize_content, acronyms
from djangae.test import TestCase
from django.test import override_settings


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
    @skip("Atom fields not implemented")
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

        results = [x for x in index.search("test", document_class=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("TEST", document_class=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search("cheese OR pickle", document_class=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        results = [x for x in index.search('cheese OR text:pickle', document_class=Doc)]

        # Both documents should have come back
        self.assertCountEqual(
            [doc.id, doc2.id],
            [x.id for x in results]
        )

        # FIXME: Uncomment when exact matching is implemented
        # results = [x for x in index.search('"cheese" OR pickle', document_class=Doc)]

        # # Both documents should have come back
        # self.assertCountEqual(
        #   [doc.id, doc2.id],
        #   [x.id for x in results]
        # )

    def test_removing_document(self):

        class Doc(Document):
            text = fields.TextField()

        i0 = Index(name="index1")
        i1 = Index(name="index2")

        d0 = i0.add(Doc(text="One"))

        # One field, one token
        self.assertEqual(
            TokenFieldIndex.objects.count(),
            1
        )

        self.assertEqual(i0.document_count(), 1)
        self.assertEqual(i1.document_count(), 0)

        d1 = i0.add(Doc(text="Two"))

        # Two fields, one token each
        self.assertEqual(
            TokenFieldIndex.objects.count(),
            2
        )

        self.assertEqual(i0.document_count(), 2)
        self.assertEqual(i1.document_count(), 0)

        d2 = i1.add(Doc(text="Three 3"))

        # Three fields, one token each except last which has 2
        self.assertEqual(
            TokenFieldIndex.objects.count(),
            4
        )

        self.assertEqual(i0.document_count(), 2)
        self.assertEqual(i1.document_count(), 1)

        self.assertTrue(i0.remove(d0))
        self.assertFalse(i0.remove(d0))

        self.process_task_queues()

        self.assertEqual(i0.document_count(), 1)
        self.assertEqual(i1.document_count(), 1)

        self.assertEqual(
            TokenFieldIndex.objects.count(),
            3
        )

        self.assertFalse([x for x in i0.search("text:One", Doc)])

        self.assertTrue(i0.remove(d1))

        self.process_task_queues()

        self.assertEqual(i0.document_count(), 0)
        self.assertEqual(i1.document_count(), 1)

        self.assertEqual(
            TokenFieldIndex.objects.count(),
            2
        )

        self.assertFalse([x for x in i0.search("text:Two", Doc)])

        self.assertTrue(i1.remove(d2))
        self.process_task_queues()

        self.assertEqual(i0.document_count(), 0)
        self.assertEqual(i1.document_count(), 0)

        self.assertEqual(
            TokenFieldIndex.objects.count(),
            0
        )

        self.assertFalse([x for x in i1.search("text:Three", Doc)])
        self.assertFalse([x for x in i1.search("text:3", Doc)])

    def test_pipe_not_indexed(self):
        """
            The | symbols is used for TokenFieldIndex key generation
            so shouldn't be indexed... ever!
        """

        class Doc(Document):
            name = fields.TextField()

        index = Index(name="test")
        index.add(Doc(name="|| Pipes"))

        self.assertEqual(index.document_count(), 1)
        self.assertEqual(TokenFieldIndex.objects.count(), 1)  # Just "pipes"

    def test_null_validation(self):
        """
            If a field is marked as null=False, and someone tries to index
            None, then an IntegrityError should throw. None of the documents
            should be indexed if one of them is invalid.
        """

        class Doc(Document):
            text = fields.TextField(null=False)

        index = Index("test")
        doc1 = Doc(text="test")
        doc2 = Doc(text=None)

        self.assertRaises(fields.IntegrityError, index.add, [doc1, doc2])
        self.assertEqual(index.document_count(), 0)  # Nothing should've been indexed

    def test_field_index_flag_respected(self):
        class Doc(Document):
            text = fields.TextField()
            other_text = fields.TextField(index=False)

        index = Index("test")
        doc1 = Doc(text="foo", other_text="bar")
        doc2 = Doc(text="bar", other_text="foo")

        index.add([doc1, doc2])

        results = list(index.search("foo", Doc))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "foo")
        self.assertEqual(results[0].other_text, "bar")

        results = list(index.search("bar", Doc))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].text, "bar")
        self.assertEqual(results[0].other_text, "foo")

    def test_stopwords_indexed(self):
        """
            Stop words should be indexed. They should be ranked lower
            and not included in searches if match_stopwords is False
        """

        class Doc(Document):
            text = fields.TextField()

        index = Index("test")
        doc1 = Doc(text="about")
        index.add(doc1)

        self.assertTrue(list(index.search("about", Doc)))
        self.assertTrue(list(index.search("abo", Doc, use_startswith=True)))
        self.assertFalse(list(index.search("about", Doc, match_stopwords=False)))

        # Startswith matching overrides matching of stopwords (as other tokens may start with the stop word)
        self.assertTrue(list(index.search("about", Doc, use_startswith=True, match_stopwords=False)))

    def test_document_revision(self):
        """
            Revisions exist to counter the problem that deletion from
            the index may take some time. The revision is replicated onto
            index entries so that new indexes can be created while old ones
            are being deleted.

            It doesn't protect against the eventual consistency of searching,
            it just means that we don't need to index inline.
        """

        class Doc(Document):
            text = fields.TextField()

        index = Index("test")
        doc1 = Doc(text="about")

        index.add(doc1)
        self.assertTrue(doc1.persisted)

        rev = doc1.revision

        self.assertIsNotNone(rev)
        self.assertEqual(TokenFieldIndex.objects.filter(record_id=doc1.id).count(), 1)

        # Adding an existing document again will update the revision
        index.add(doc1)
        self.assertNotEqual(doc1.revision, rev)
        rev = doc1.revision

        self.assertEqual(TokenFieldIndex.objects.count(), 2)
        self.assertEqual(TokenFieldIndex.objects.filter(record_id=doc1.id, revision=doc1.revision).count(), 1)

        # Remove then re-add should reset the revision
        self.assertEqual(index.remove(doc1), 1)

        index.add(doc1)
        self.assertNotEqual(doc1.revision, rev)

        self.assertEqual(TokenFieldIndex.objects.count(), 3)
        self.assertEqual(TokenFieldIndex.objects.filter(record_id=doc1.id, revision=doc1.revision).count(), 1)

        # Clean up everything
        self.process_task_queues()

        self.assertEqual(TokenFieldIndex.objects.count(), 1)

    @mock.patch('djangae.contrib.search.index.defer_iteration_with_finalize')
    def test_search_queue_add_to_index_does_not_defer(self, defer_mock):

        class Doc(Document):
            text = fields.TextField()

        index = Index("test")
        doc1 = Doc(text="about")

        index.add(doc1)
        self.assertTrue(doc1.persisted)

        self.process_task_queues()

        self.assertFalse(defer_mock.called)

    @mock.patch('djangae.contrib.search.index.defer_iteration_with_finalize')
    def test_search_queue_reindex_call_defer(self, defer_mock):

        class Doc(Document):
            text = fields.TextField()

        index = Index("test")
        doc1 = Doc(text="about")

        index.add(doc1)
        # Adding an existing document again will update the revision
        index.add(doc1)
        self.assertTrue(doc1.persisted)

        self.process_task_queues()
        defer_mock.assert_called_with(mock.ANY, mock.ANY, mock.ANY, _queue="default", _shards=1)

    @override_settings(DJANGAE_SEARCH_QUEUE="search")
    @mock.patch('djangae.contrib.search.index.defer_iteration_with_finalize')
    def test_search_queue_reindex_queue_override(self, defer_mock):

        class Doc(Document):
            text = fields.TextField()

        index = Index("test")
        doc1 = Doc(text="about")

        index.add(doc1)
        # Adding an existing document again will update the revision
        index.add(doc1)
        self.assertTrue(doc1.persisted)

        self.process_task_queues()
        defer_mock.assert_called_with(mock.ANY, mock.ANY, mock.ANY, _queue="default", _shards=1)


class TokenizingTests(TestCase):
    def test_tokenization_of_acronyms(self):
        """
            Hyphens are stop characters except when they are part
            of an ancronym (e.g I-B-M), this handling also covers dates
            (e.g. 2020-01-01)
        """
        text = "This-is some text with - hyphens. I-B-M"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["This", "is", "Thisis", "This-is", "some", "text", "with", "hyphens",
             "hyphens.", "I-B-M", "IBM", "I.B.M", "I", "B", "M"]
        )

    def test_tokenization_of_special_symbols_within_a_word(self):
        """
            Symbols configured in `PUNCTUATION` and `SPECIAL_SYMBOLS` constants
            are considered stop words characters, but they do not count as token
            themselves.
            (e.g. "l'oreal" would generate ["l", "oreal", "l'oreal", "loreal"])
        """

        "`'` is configured in `SPECIAL_SYMBOLS`"
        text = "l'oreal"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["l", "oreal", "l'oreal", "loreal"]
        )

        text = "H*M"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["H", "M", "HM", "H*M"]
        )

    def test_tokenization_of_generic_symbols_within_a_word(self):
        """
            Symbols that are not listed in `PUNCTUATION` or `SPECIAL_SYMBOLS` constants
            are considered normal characters and they won't be stopwords
            (e.g. "H&M" would generate ["H&M"])
        """
        text = "H&M"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["H&M", "HM"]
        )

    def test_tokenization_of_symbols_as_word_on_its_own(self):
        """
            Symbols on their own are not considered tokens
            (e.g. "H & M" would generate ["H", "M"])
        """
        text = "H & M"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["H", "M"]
        )
        text = "Hello!"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["Hello", "Hello!"]
        )

    def test_tokenization_of_repeated_words(self):
        """
            Hyphens are stop characters except when they are part
            of an ancronym (e.g I-B-M), this handling also covers dates
            (e.g. 2020-01-01)
        """
        text = "du du du da da da"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["du", "da"]
        )

    def test_tokenization_of_not_acronyms(self):
        """
            Words than have more than 1 letter and separated by an
            hyphen are not an acronym.
        """
        text = "This-is-not-an-acronym"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["This", "is", "not", "an", "acronym", "This-is-not-an-acronym", "Thisisnotanacronym"]
        )

    def test_tokenization_of_not_acronyms_pipes(self):
        """
            When a word contains WORD_DOCUMENT_JOIN_STRING special char,
            it's replaced by an EMPTY char.
        """
        text = "Tokenize    multiple chars ||"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["Tokenize", "multiple", "chars"]
        )

    def test_tokenization_of_word_multiple_symbols(self):
        """
            When tokenizing a word, we also save its version with no symbols
        """
        text = "[[[[Tokenize]]]]"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["[[[[Tokenize]]]]", "[[[[Tokenize", "Tokenize]]]]", "Tokenize"]
        )

    def test_tokenization_of_dates(self):
        """
            Hyphens are stop characters except when they are part
            of a date
            (e.g. 2020-01-01)
        """
        text = "This is a date 2020-01-02"
        tokens = tokenize_content(text)
        self.assertCountEqual(
            tokens,
            ["This", "is", "a", "date", "2020-01-02", "20200102", "2020.01.02", "2020", "01", "02"]
        )

    def test_acronyms_not_an_acronym(self):
        """
            Words longer than one character which are separated by stop characters
            should not be an acronym.
        """
        text = "This-is-not-an-acronym"
        acronyms_list = acronyms(text)
        self.assertEqual(len(acronyms_list), 0)

    def test_acronyms_is_an_acronym(self):
        """
            Consistent stop characters should generate acronyms
            (e.g I.B-M)
        """
        text = "I.B.M"
        acronyms_list = acronyms(text)
        self.assertCountEqual(acronyms_list, ["IBM", "I-B-M"])
        self.assertTrue("IBM" in acronyms_list)
        self.assertTrue("I-B-M" in acronyms_list)

    def test_acronyms_not_an_acronym_different_symbols(self):
        """
            Mixed stop characters should not be generate acronyms
            (e.g I.B-M)
        """
        text = "I.B-M"
        acronyms_list = acronyms(text)
        self.assertEqual(len(acronyms_list), 0)

    def test_acronyms_is_an_acronym_date(self):
        """
            Consisent stop characters should generate acronyms in a date
            (e.g. 2022-01-06)
        """
        text = "2022-01-06"
        acronyms_list = acronyms(text)
        self.assertCountEqual(acronyms_list, ["2022.01.06", "20220106"])
        self.assertTrue("2022.01.06" in acronyms_list)
        self.assertTrue("20220106" in acronyms_list)

    def test_acronyms_not_an_acronym_date(self):
        """
            Mixed stop characters should not be generate acronyms for a date
            (e.g. 2022-01.06)
        """
        text = "2022-01.06"
        acronyms_list = acronyms(text)
        self.assertEqual(len(acronyms_list), 0)
