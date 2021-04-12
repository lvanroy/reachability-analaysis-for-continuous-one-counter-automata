import unittest

from automaton.DotReader import DotReader


class TestBasicGraph(unittest.TestCase):
    def test_graph_without_edges(self):
        reader = DotReader("test/automaton/input/no_edges.dot")
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 4)

        nodes = automaton.nodes

        self.assertEqual(list(nodes.keys()), ["Q0", "Q1", "Q2", "Q3"])

        self.assertEqual(automaton.get_node_label("Q0"), "CompilationUnit")
        self.assertEqual(automaton.get_node_label("Q1"), "Function Definition")
        self.assertEqual(automaton.get_node_label("Q2"), "Type Specifier")

    def test_graph_without_node_specification(self):
        reader = DotReader("test/automaton/input/no_nodes.dot")
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_edges(), 4)

        self.assertTrue(automaton.edge_exists("Q0", "Q1"))
        self.assertTrue(automaton.edge_exists("Q1", "Q2"))
        self.assertTrue(automaton.edge_exists("Q2", "Q3"))
        self.assertTrue(automaton.edge_exists("Q3", "Q4"))
        self.assertTrue(automaton.edge_exists("Q2", "Q4"))

        self.assertEqual(automaton.get_edge_label("Q2", "Q4"), "this is a random label")
