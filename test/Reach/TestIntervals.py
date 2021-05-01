import unittest

from Reach.Interval import Interval
from Reach.Intervals import Intervals


class TestIntervals(unittest.TestCase):
    def test_interval_creation(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        intervals = Intervals(0, False, 10, True)
        self.assertEqual("(0, 10]", str(intervals))

        intervals = Intervals(0, True, 10, False)
        self.assertEqual("[0, 10)", str(intervals))

        intervals = Intervals(0, False, 10, False)
        self.assertEqual("(0, 10)", str(intervals))

    def test_simple_add(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        addend = Intervals(0, False, 5, True)
        intervals.add(addend)
        self.assertEqual("(0, 15]", str(intervals))

    def test_contained_union(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        uniend = Intervals(0, False, 5, False)
        intervals.union(uniend)
        self.assertEqual("[0, 10]", str(intervals))

    def test_left_extension_union(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        uniend = Intervals(-5, False, 0, False)
        intervals.union(uniend)
        self.assertEqual("(-5, 10]", str(intervals))

        uniend = Intervals(-5, True, 0, False)
        intervals.union(uniend)
        self.assertEqual("[-5, 10]", str(intervals))

    def test_right_extension_union(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        uniend = Intervals(0, False, 15, False)
        intervals.union(uniend)
        self.assertEqual("[0, 15)", str(intervals))

        uniend = Intervals(15, False, 15, True)
        intervals.union(uniend)
        self.assertEqual("[0, 15]", str(intervals))

    def test_new_interval_union(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        uniend = Intervals(15, False, 16, False)
        intervals.union(uniend)
        self.assertEqual("[0, 10] (15, 16)", str(intervals))

        uniend = Intervals(-5, False, -3, False)
        intervals.union(uniend)
        self.assertEqual("(-5, -3) [0, 10] (15, 16)", str(intervals))

        uniend = Intervals(13, True, 14, True)
        intervals.union(uniend)
        self.assertEqual("(-5, -3) [0, 10] [13, 14] (15, 16)", str(intervals))

    def test_merge_multiple_union(self):
        intervals = Intervals(0, True, 10, True)
        self.assertEqual("[0, 10]", str(intervals))

        uniend = Intervals(15, False, 16, False)
        intervals.union(uniend)
        self.assertEqual("[0, 10] (15, 16)", str(intervals))

        uniend = Intervals(-15, False, 16, False)
        intervals.union(uniend)
        self.assertEqual("(-15, 16)", str(intervals))

