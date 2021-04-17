import unittest

from automaton.DotReader import DotReader


class TestCreateAutomaton(unittest.TestCase):
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

        self.assertEqual(automaton.get_nr_of_edges(), 5)

        self.assertTrue(automaton.edge_exists("Q0", "Q1"))
        self.assertTrue(automaton.edge_exists("Q1", "Q2"))
        self.assertTrue(automaton.edge_exists("Q2", "Q3"))
        self.assertTrue(automaton.edge_exists("Q3", "Q4"))
        self.assertTrue(automaton.edge_exists("Q2", "Q4"))

        self.assertEqual(automaton.get_edge_label("Q2", "Q4"), "this is a random label")

    def test_graph_edges(self):
        reader = DotReader("test/automaton/input/simple_graph.dot")
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_edges(), 7)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertEqual("+0", automaton.get_edge_label("q1", "q2"))
        self.assertEqual("+20", automaton.get_edge_label("q2", "q3"))
        self.assertEqual("+1", automaton.get_edge_label("q3", "q1"))
        self.assertEqual("+0", automaton.get_edge_label("q1", "q4"))
        self.assertEqual("-20", automaton.get_edge_label("q4", "q5"))
        self.assertEqual("+1", automaton.get_edge_label("q5", "q1"))

        self.assertEqual("<=15", automaton.get_node_label("q2"))
        self.assertEqual(">=20", automaton.get_node_label("q3"))
        self.assertEqual(">=20", automaton.get_node_label("q4"))
        self.assertEqual("<=10", automaton.get_node_label("q5"))
