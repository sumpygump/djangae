import re
from .constants import SPLIT_RE


def tokenize_content(content):
    """
        We inherit the rules from the App Engine Search API
        when it comes to punctuation.

        We have a list of punctuation chars which break the
        content into tokens, and then some special cases where it
        makes sense. You can find the rules documented here:
        https://cloud.google.com/appengine/docs/standard/python/search#special-treatment
    """

    return re.split(SPLIT_RE, content)
