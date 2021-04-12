import unittest

from automaton.DotReader import DotReader


class TestBasicGraph(unittest.TestCase):
    def test_graph_without_edges(self):
        reader = DotReader("test/automaton/input/no_edges.dot")
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 4)

        nodes = automaton.nodes

        self.assertEqual(nodes.keys(), ["Q0", "Q1", "Q2", "Q3"])

