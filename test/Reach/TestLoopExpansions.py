import unittest
import os

from typing import Dict, Tuple

from Reach.ReachManager import ReachManager

from Automaton.DotReader import DotReader
from Automaton.LoopFinder import Loop


class TestLoopExpansion(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def initialise_automaton(self, file_name):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        self.automaton = reader.create_automaton()

        self.manager = ReachManager(self.automaton)

    def assert_expansions_match(self, expected):
        self.assertEqual(expected, self.manager.get_up_expansions())

    def test_simple_loop(self):
        self.initialise_automaton("input/simple_automaton.dot")

        expected: Dict[Loop, int] = dict()
        loop = self.automaton.get_loops()[0]
        expected[loop] = 0
        self.assert_expansions_match(expected)

        self.manager.update_automaton()

        self.assert_expansions_match(expected)

        self.manager.update_automaton()

        self.assert_expansions_match(expected)

        self.manager.update_automaton()

        expected[loop] = 1
        self.assert_expansions_match(expected)
