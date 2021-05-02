import unittest
import os

from Automaton.DotReader import DotReader
from Automaton.LoopFinder import LoopFinder


class TestLoopFinder(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def test_no_loop(self):
        file_name = self.build_file_path("input/no_loop.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        loop_finder = LoopFinder(automaton)
        loop_finder.find_loops()

        self.assertFalse(loop_finder.get_loops())

    def test_simple_loop(self):
        file_name = self.build_file_path("input/simple_loop.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        loop_finder = LoopFinder(automaton)
        loop_finder.find_loops()

        loops = loop_finder.get_loops()
        self.assertTrue(len(loops) == 1)
        self.assertEqual(["s0", "s1", "s2"], loops[0])

    def test_nested_loop(self):
        file_name = self.build_file_path("input/nested_loop.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        loop_finder = LoopFinder(automaton)
        loop_finder.find_loops()

        loops = loop_finder.get_loops()
        self.assertTrue(len(loops) == 2)
        self.assertEqual(["s0", "s1"], loops[0])
        self.assertEqual(["s0", "s1", "s2"], loops[1])


