import unittest
import os

from Reach.ReachManager import ReachManager

from Automaton.DotReader import DotReader


class TestLoopAcceleration(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def initialise_automaton(self, file_name):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        self.automaton = reader.create_automaton()

        self.manager = ReachManager(self.automaton)

    def assert_interval_matches(self, state, origin, expected):
        interval = self.manager.get_interval(state, origin)
        if expected is not None:
            self.assertEqual(expected, str(interval))
        else:
            self.assertIsNone(interval)

    def test_accel_loop_upper_with_no_bounds(self):
        self.initialise_automaton("input/simple_unbounded_upwards_loop.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, inf)")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, inf)")
        self.assert_interval_matches("Q0", "Q1", "(0, inf)")

    def test_accel_loop_up_with_bounds(self):
        self.initialise_automaton("input/simple_bounded_upwards_loop.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 6]")
        self.assert_interval_matches("Q0", "Q1", "(0, 200]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 202]")
        self.assert_interval_matches("Q0", "Q1", "(0, 200]")

    def test_accel_loop_down_with_no_bounds(self):
        self.initialise_automaton("input/simple_unbounded_downwards_loop.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-inf, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-inf, 0)")
        self.assert_interval_matches("Q0", "Q1", "(-inf, 0)")

    def test_accel_loop_down_with_bounds(self):
        self.initialise_automaton("input/simple_bounded_downwards_loop.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-202, 0)")

    def test_accel_loop_up_down_with_no_bounds(self):
        self.initialise_automaton(
            "input/simple_unbounded_upwards_downwards_loop.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", "(-2, 2)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-inf, inf)")
        self.assert_interval_matches("Q0", "Q1", "(-2, 2)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-inf, inf)")
        self.assert_interval_matches("Q0", "Q1", "(-inf, inf)")

    def test_accel_intersecting_loop_up(self):
        self.initialise_automaton("input/simple_double_loop_up.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", None)
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", "(0, 1]")
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")
        self.assert_interval_matches("Q2", "Q0", "(0, 1]")
        self.assert_interval_matches("Q3", "Q2", "(0, 2]")
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")
        self.assert_interval_matches("Q2", "Q0", "(0, 5]")
        self.assert_interval_matches("Q3", "Q2", "(0, 2]")
        self.assert_interval_matches("Q0", "Q3", "(0, 3]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 202]")
        self.assert_interval_matches("Q2", "Q0", "(0, 400]")
        self.assert_interval_matches("Q3", "Q2", "(0, 6]")
        self.assert_interval_matches("Q0", "Q3", "(0, 3]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 202]")
        self.assert_interval_matches("Q2", "Q0", "(0, 400]")
        self.assert_interval_matches("Q3", "Q2", "(0, 401]")
        self.assert_interval_matches("Q0", "Q3", "(0, 7]")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 202]")
        self.assert_interval_matches("Q2", "Q0", "(0, 400]")
        self.assert_interval_matches("Q3", "Q2", "(0, 401]")
        self.assert_interval_matches("Q0", "Q3", "(0, 402]")

    def test_accel_intersecting_loop_down(self):
        self.initialise_automaton("input/simple_double_loop_down.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", None)
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-4, 0)")
        self.assert_interval_matches("Q2", "Q0", "[-5, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-202, 0)")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-6, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-202, 0)")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-7, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[-200, 0)")
        self.assert_interval_matches("Q0", "Q1", "[-202, 0)")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 0)")

    def test_accel_intersecting_loop_up_down(self):
        self.initialise_automaton("input/simple_double_loop_up_down.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", None)
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 2]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(0, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 4]")
        self.assert_interval_matches("Q2", "Q0", "[-1, 4)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-3, 200]")
        self.assert_interval_matches("Q0", "Q1", "(0, 202]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 4)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 4)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-3, 200]")
        self.assert_interval_matches("Q0", "Q1", "(-3, 202]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 202)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 4)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 4)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-3, 200]")
        self.assert_interval_matches("Q0", "Q1", "(-3, 202]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 202)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 202)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 4)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-402, 200]")
        self.assert_interval_matches("Q0", "Q1", "(-3, 202]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 202)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 202)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 202)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "(-402, 200]")
        self.assert_interval_matches("Q0", "Q1", "(-402, 202]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 202)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 202)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 202)")

    def test_accel_intersecting_loop_eq(self):
        self.initialise_automaton("input/simple_double_loop_eq.dot")
        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", None)
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", None)
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", None)
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", None)
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-1, 0)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", None)

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-1, 0) (3, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0) (3, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-2, 0) (2, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0) (3, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 0) (2, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-3, 0) (1, 8)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0) (0, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 0) (2, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 0) (1, 8)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0) (0, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 0) (1, 8)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 0) (0, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 8)")

        self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[4, 4]")
        self.assert_interval_matches("Q0", "Q1", "(4, 8]")
        self.assert_interval_matches("Q2", "Q0", "[-400, 8)")
        self.assert_interval_matches("Q3", "Q2", "[-401, 8)")
        self.assert_interval_matches("Q0", "Q3", "[-402, 8)")
