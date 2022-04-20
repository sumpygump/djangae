import sleuth
from django.db import models

from djangae.processing import sequential_int_key_ranges
from djangae.test import TestCase


class TestModel(models.Model):
    pass


class ProcessingTestCase(TestCase):
    def test_sequential_int_key_ranges(self):
        with sleuth.fake("django.db.models.query.QuerySet.first", return_value=0):
            with sleuth.fake("django.db.models.query.QuerySet.last", return_value=1000):
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

    def test_sequential_int_key_ranges_non_zero_first(self):
        with sleuth.fake("django.db.models.query.QuerySet.first", return_value=900):
            with sleuth.fake("django.db.models.query.QuerySet.last", return_value=1000):
                ranges = sequential_int_key_ranges(TestModel.objects.all(), 1)
                self.assertEqual(ranges, [(900, 1001)])

                ranges = sequential_int_key_ranges(TestModel.objects.all(), 10)
                self.assertEqual(ranges[0], (900, 910))
                self.assertEqual(ranges[1], (910, 920))
                self.assertEqual(ranges[-1], (990, 1001))
                self.assertEqual(len(ranges), 10)

                ranges = sequential_int_key_ranges(TestModel.objects.all(), 2000)
                self.assertEqual(ranges[0], (900, 901))
                self.assertEqual(ranges[1], (901, 902))
                self.assertEqual(ranges[-1], (999, 1001))
                self.assertEqual(len(ranges), 100)

    def test_sequential_int_key_ranges_negative_first(self):
        with sleuth.fake("django.db.models.query.QuerySet.first", return_value=-1000):
            with sleuth.fake("django.db.models.query.QuerySet.last", return_value=1000):
                ranges = sequential_int_key_ranges(TestModel.objects.all(), 1)
                self.assertEqual(ranges, [(-1000, 1001)])

                ranges = sequential_int_key_ranges(TestModel.objects.all(), 200)
                self.assertEqual(ranges[0], (-1000, -990))
                self.assertEqual(ranges[1], (-990, -980))
                self.assertEqual(ranges[-1], (990, 1001))
                self.assertEqual(len(ranges), 200)

                ranges = sequential_int_key_ranges(TestModel.objects.all(), 4000)
                self.assertEqual(ranges[0], (-1000, -999))
                self.assertEqual(ranges[1], (-999, -998))
                self.assertEqual(ranges[-1], (999, 1001))
                self.assertEqual(len(ranges), 2000)
