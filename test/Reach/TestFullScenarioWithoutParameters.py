import unittest
import os

from Automaton.DotReader import DotReader

from Reach.ReachManager import ReachManager


class TestFullScenarioWithoutParamters(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def initialise_automaton(self, file_name,
                             min=-float('inf'), max=float('inf'), initial=0):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        automaton = reader.create_automaton()
        automaton.set_lower_bound(min)
        automaton.set_upper_bound(max)
        automaton.set_initial_value(initial)

        self.manager = ReachManager(automaton)

    def assert_interval_matches(self, state, origin, expected):
        interval = self.manager.get_interval(state, origin)
        if expected is not None:
            self.assertEqual(expected, str(interval))
        else:
            self.assertIsNone(interval)

    def test_simple_automaton(self):
        self.initialise_automaton("input/simple_automaton.dot")

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s2", "(0, inf)")
        self.assert_interval_matches("s2", "s1", "(0, inf)")

    def test_bounded_node(self):
        self.initialise_automaton("input/one_node_bounded_automaton.dot")

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", "(0, 201]")
        self.assert_interval_matches("s1", "s0", "(0, 200]")
        self.assert_interval_matches("s1", "s2", "(0, 200]")
        self.assert_interval_matches("s2", "s1", "(0, 201]")

    def test_bounded_automaton(self):
        self.initialise_automaton("input/one_node_bounded_automaton.dot",
                                  -50, 150)

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", "(0, 150]")
        self.assert_interval_matches("s1", "s0", "(0, 150]")
        self.assert_interval_matches("s1", "s2", "(0, 150]")
        self.assert_interval_matches("s2", "s1", "(0, 150]")

    def test_impossible_automaton(self):
        self.initialise_automaton("input/one_node_bounded_automaton.dot",
                                  50, 150)

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("s0", "s0", None)
        self.assert_interval_matches("s0", "s1", None)
        self.assert_interval_matches("s1", "s0", None)
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", None)

        self.assertFalse(self.manager.is_reachable("s0"))
        self.assertFalse(self.manager.is_reachable("s1"))
        self.assertFalse(self.manager.is_reachable("s2"))

    def test_mutated_initial_value(self):
        self.initialise_automaton("input/one_node_bounded_automaton.dot",
                                  -50, 150, 5)

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("s0", "s0", "[5, 5]")
        self.assert_interval_matches("s0", "s1", "(5, 150]")
        self.assert_interval_matches("s1", "s0", "(5, 150]")
        self.assert_interval_matches("s1", "s2", "(5, 150]")
        self.assert_interval_matches("s2", "s1", "(5, 150]")

        self.assertTrue(self.manager.is_reachable("s0"))
        self.assertTrue(self.manager.is_reachable("s1"))
        self.assertTrue(self.manager.is_reachable("s2"))

    def test_downwards_acceleration(self):
        self.initialise_automaton("input/downwards _acceleration_example.dot")

        while not self.manager.is_finished():
            self.manager.update_automaton()

        self.assert_interval_matches("Q0", "Q0", "[0, 0]")
        self.assert_interval_matches("Q1", "Q0", "[0, 0]")
        self.assert_interval_matches("Q2", "Q1", "[0, 0]")
        self.assert_interval_matches("Q2", "Q15", "(-inf, inf)")
        self.assert_interval_matches("Q15", "Q2", "(-inf, inf)")
        self.assert_interval_matches("Q6", "Q2", "(-inf, inf)")
        self.assert_interval_matches("_0", "Q6", "[5, 5]")
        self.assert_interval_matches("Q7", "_0", "[5, 5]")
        self.assert_interval_matches("Q8", "Q7", "[5, 5]")
        self.assert_interval_matches("Q8", "Q7", "[5, 5]")
        self.assert_interval_matches("Q9", "Q6", "(-inf, inf)")
        self.assert_interval_matches("_1", "Q9", "(-inf, 5]")
        self.assert_interval_matches("Q10", "_1", "(-inf, 5]")
        self.assert_interval_matches("Q13", "Q10", "(-inf, 5)")
        self.assert_interval_matches("Q12", "_2", "[5, inf)")
        self.assert_interval_matches("Q14", "Q13", "(-inf, 5) (5, inf)")
        self.assert_interval_matches("Q11", "Q6", "(-inf, inf)")
        self.assert_interval_matches("_2", "Q11", "[5, inf)")
        self.assert_interval_matches("Q13", "Q12", "(5, inf)")
