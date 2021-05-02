import unittest
import os

from typing import Dict, Tuple

from Reach.ReachManager import ReachManager

from Automaton.DotReader import DotReader


class TestLoopExpansion(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def initialise_automaton(self, file_name):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.manager = ReachManager(automaton)

    def assert_expansions_match(self, expected):
        self.assertEqual(expected, self.manager.get_expansions())

    def test_simple_loop(self):
        self.initialise_automaton("input/simple_automaton.dot")

        expected: Dict[Tuple[str, ...], int] = dict()
        expected[("s1", "s2")] = 0
        self.assert_expansions_match(expected)

        self.manager.post_automaton()

        self.assert_expansions_match(expected)

        self.manager.post_automaton()

        self.assert_expansions_match(expected)

        self.manager.post_automaton()

        expected[("s1", "s2")] = 1
        self.assert_expansions_match(expected)
