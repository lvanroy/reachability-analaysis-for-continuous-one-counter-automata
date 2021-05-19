import unittest

from Reach.Intervals import Intervals


class TestIntervalUnion(unittest.TestCase):
    def initialise_intervals(self, low, incl_low, high, incl_high):
        self.intervals = Intervals(low, incl_low, high, incl_high)

    def union(self, low, incl_low, high, incl_high):
        interval = Intervals(low, incl_low, high, incl_high)
        self.intervals.union(interval)

    def assert_interval_matches(self, expected):
        if expected is not None:
            self.assertEqual(expected, str(self.intervals))
        else:
            self.assertIsNone(self.intervals)

    def test_union_no_overlap(self):
        self.initialise_intervals(-100, True, 100, False)
        self.assert_interval_matches("[-100, 100)")

        self.union(200, True, 300, True)
        self.assert_interval_matches("[-100, 100) [200, 300]")

    def test_union_equivalent(self):
        self.initialise_intervals(-100, True, 100, True)
        self.assert_interval_matches("[-100, 100]")

        self.union(-100, True, 100, True)
        self.assert_interval_matches("[-100, 100]")

    def test_union_overlap_lower(self):
        self.initialise_intervals(100, False, 200, True)
        self.assert_interval_matches("(100, 200]")

        self.union(150, True, 300, False)
        self.assert_interval_matches("(100, 300)")

    def test_union_overlap_upper(self):
        self.initialise_intervals(-20, False, -10, True)
        self.assert_interval_matches("(-20, -10]")

        self.union(-10, True, 300, False)
        self.assert_interval_matches("(-20, 300)")

    def test_union_overlap_on_bound(self):
        self.initialise_intervals(20, True, 50, True)
        self.assert_interval_matches("[20, 50]")

        self.union(50, False, 100, False)
        self.assert_interval_matches("[20, 100)")

        self.union(100, True, 150, False)
        self.assert_interval_matches("[20, 150)")

    def test_union_with_both_intervals_extensions(self):
        self.initialise_intervals(-1127, False, 5, False)
        self.assert_interval_matches("(-1127, 5)")

        self.union(5, False, 614, False)
        self.assert_interval_matches("(-1127, 5) (5, 614)")

        self.union(5, False, 613, False)
        self.assert_interval_matches("(-1127, 5) (5, 614)")
