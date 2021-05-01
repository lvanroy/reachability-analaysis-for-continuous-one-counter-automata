import unittest
import os

from Reach.ReachManager import ReachManager

from automaton.DotReader import DotReader


class TestPostUpdate(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def initialise_automaton(self, file_name):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.manager = ReachManager(automaton)

    def assert_interval_matches(self, state, origin, expected):
        interval = self.manager.get_interval(state, origin)
        if expected is not None:
            self.assertEqual(expected, str(interval))
        else:
            self.assertIsNone(interval)

    def test_simple_scenario(self):
        self.initialise_automaton("input/simple_automaton.dot")
        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", None)
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", None)

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", None)

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", "(0, 1]")

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s2", "(0, 2]")
        self.assert_interval_matches("s2", "s1", "(0, 1]")

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s0", "[0, 0]")
        self.assert_interval_matches("s1", "s2", "(0, 2]")
        self.assert_interval_matches("s2", "s1", "(0, 3]")

    def test_bounded_scenario(self):
        self.initialise_automaton("input/bounded_automaton.dot")
        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", None)
        self.assert_interval_matches("s1", "s0", None)
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", None)

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", None)
        self.assert_interval_matches("s1", "s0", "(0, 1]")
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", None)

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", "(0, 2]")
        self.assert_interval_matches("s1", "s0", "(0, 1]")
        self.assert_interval_matches("s1", "s2", None)
        self.assert_interval_matches("s2", "s1", "(0, 2]")

        self.manager.post_automaton()

        self.assert_interval_matches("s0", "s0", "[0, 0]")
        self.assert_interval_matches("s0", "s1", "(0, 2]")
        self.assert_interval_matches("s1", "s0", "(0, 2]")
        self.assert_interval_matches("s1", "s2", "(0, 2]")
        self.assert_interval_matches("s2", "s1", "(0, 2]")
