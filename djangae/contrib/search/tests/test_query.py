from djangae.test import TestCase
from djangae.contrib.search.query import _tokenize_query_string


class QueryTests(TestCase):
    def test_tokenization_breaks_at_punctuation(self):
        q = "hi, there is a 100% chance this works [honest]"

        tokens = _tokenize_query_string(q)
        kinds = set(x[0] for x in tokens)
        words = [x[-1] for x in tokens]

        self.assertEqual(kinds, {"word"})  # All tokens should be recognised as words
        self.assertEqual(words, ["hi", "100", "chance", "works", "honest"])
