import os
import re

from djangae.environment import (
    app_host,
    is_development_environment,
    is_production_environment,
)
from djangae.test import TestCase


class EnvironmentUtilsTest(TestCase):

    def test_is_production_environment(self):
        self.assertFalse(is_production_environment())
        os.environ["GAE_ENV"] = 'standard'
        self.assertTrue(is_production_environment())
        del os.environ["GAE_ENV"]

    def test_is_development_environment(self):
        self.assertTrue(is_development_environment())
        os.environ["GAE_ENV"] = 'standard'
        self.assertFalse(is_development_environment())
        del os.environ["GAE_ENV"]

    def test_app_host(self):
        # Check that this is the right kind of format
        result = app_host()
        self.assertMatchesRegex(r"[a-z0-9]+-dot-[a-z0-9]+\.appspot.com", result)

    def assertMatchesRegex(self, regex, string):
        # We say "match", but we use re.search because re.match will only match from the start of
        # the string
        if not re.search(regex, string):
            raise AssertionError(f"String '{string}' does not match regular expression '{regex}'.")
