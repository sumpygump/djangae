import sleuth
from django.db import models

from djangae.processing import sequential_int_key_ranges
from djangae.test import (
    TaskFailedBehaviour,
    TestCase,
)

class TestModel(models.Model):
    pass

class ProcessingTestCase(TestCase):
    def test_sequential_int_key_ranges(self):
        with sleuth.fake(
            "django.db.models.query.QuerySet.values", return_value=[{"pk": 1000}]
        ):
            ranges = sequential_int_key_ranges(TestModel.objects.all(), 1)
            self.assertEqual(ranges, [(0, 1001)])

            ranges = sequential_int_key_ranges(TestModel.objects.all(), 100)
            self.assertEqual(ranges[0], (0, 10))
            self.assertEqual(ranges[1], (10, 20))
            self.assertEqual(ranges[-1], (990, 1001))
            self.assertEqual(len(ranges), 100)

            ranges = sequential_int_key_ranges(TestModel.objects.all(), 2000)
            self.assertEqual(ranges[0], (0, 1))
            self.assertEqual(ranges[1], (1, 2))
            self.assertEqual(ranges[-1], (999, 1001))
            self.assertEqual(len(ranges), 1000)
