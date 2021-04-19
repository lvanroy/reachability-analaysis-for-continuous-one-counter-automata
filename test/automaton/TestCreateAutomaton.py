import unittest
import io
import os

from contextlib import redirect_stdout

from automaton.DotReader import DotReader


class TestCreateAutomaton(unittest.TestCase):
    def build_file_path(self, file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def test_graph_without_start(self):
        file_name = self.build_file_path("input/no_edges.dot")
        reader = DotReader(file_name)

        f = io.StringIO()
        with redirect_stdout(f):
            with self.assertRaises(SystemExit) as e:
                reader.create_automaton()

        self.assertEqual(e.exception.code, -1)

        out = f.getvalue()

        self.assertEqual(out,
                         "Error: no initial node was found, "
                         "make sure that there is a node with an "
                         "incoming edge originating from an invisible "
                         "node.\n")

    def test_graph_without_node_specification(self):
        file_name = self.build_file_path("input/no_node_labels.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 5)
        self.assertEqual(automaton.get_nr_of_edges(), 5)

        self.assertTrue(automaton.edge_exists("Q0", "Q1"))
        self.assertTrue(automaton.edge_exists("Q1", "Q2"))
        self.assertTrue(automaton.edge_exists("Q2", "Q3"))
        self.assertTrue(automaton.edge_exists("Q3", "Q4"))
        self.assertTrue(automaton.edge_exists("Q2", "Q4"))

        self.assertEqual(automaton.get_edge_label("Q2", "Q4"), "this is a random label")

    def test_graph_edges(self):
        file_name = self.build_file_path("input/simple_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 6)
        self.assertEqual(automaton.get_nr_of_edges(), 7)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q2")))
        self.assertEqual("+20.0", str(automaton.get_edge_operation("q2", "q3")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q3", "q1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q4")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q4", "q5")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q5", "q1")))

        self.assertEqual("<=15.0", str(automaton.get_node_condition("q2")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q3")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q4")))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

    def test_graph_normal_and_operation_labels(self):
        file_name = self.build_file_path("input/all_label_types_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 6)
        self.assertEqual(automaton.get_nr_of_edges(), 7)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q2")))
        self.assertEqual("+20.0", str(automaton.get_edge_operation("q2", "q3")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q3", "q1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q4")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q4", "q5")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q5", "q1")))

        self.assertEqual("edge1", str(automaton.get_edge_label("q0", "q1")))
        self.assertEqual("edge2", str(automaton.get_edge_label("q1", "q2")))
        self.assertEqual("edge3", str(automaton.get_edge_label("q2", "q3")))
        self.assertEqual("edge5", str(automaton.get_edge_label("q3", "q1")))
        self.assertEqual("edge4", str(automaton.get_edge_label("q1", "q4")))
        self.assertEqual("edge6", str(automaton.get_edge_label("q4", "q5")))
        self.assertEqual("edge7", str(automaton.get_edge_label("q5", "q1")))

        self.assertEqual("<=15.0", str(automaton.get_node_condition("q2")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q3")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q4")))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

        self.assertEqual("node1", str(automaton.get_node_label("q1")))
        self.assertEqual("node2", str(automaton.get_node_label("q2")))
        self.assertEqual("node3", str(automaton.get_node_label("q3")))
        self.assertEqual("node4", str(automaton.get_node_label("q4")))
        self.assertEqual("node5", str(automaton.get_node_label("q5")))

    def test_graph_with_invalid_condition(self):
        file_name = self.build_file_path("input/unsupported_condition_types_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 6)
        self.assertEqual(automaton.get_nr_of_edges(), 7)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q2")))
        self.assertEqual("+20.0", str(automaton.get_edge_operation("q2", "q3")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q3", "q1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q4")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q4", "q5")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q5", "q1")))

        self.assertEqual("edge1", str(automaton.get_edge_label("q0", "q1")))
        self.assertEqual("edge2", str(automaton.get_edge_label("q1", "q2")))
        self.assertEqual("edge3", str(automaton.get_edge_label("q2", "q3")))
        self.assertEqual("edge5", str(automaton.get_edge_label("q3", "q1")))
        self.assertEqual("edge4", str(automaton.get_edge_label("q1", "q4")))
        self.assertEqual("edge6", str(automaton.get_edge_label("q4", "q5")))
        self.assertEqual("edge7", str(automaton.get_edge_label("q5", "q1")))

        self.assertIsNone(automaton.get_node_condition("q2"))
        self.assertIsNone(automaton.get_node_condition("q3"))
        self.assertIsNone(automaton.get_node_condition("q4"))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

        self.assertEqual("node1", str(automaton.get_node_label("q1")))
        self.assertEqual("<15", str(automaton.get_node_label("q2")))
        self.assertEqual(">20", str(automaton.get_node_label("q3")))
        self.assertEqual("!=20", str(automaton.get_node_label("q4")))
        self.assertEqual("node5", str(automaton.get_node_label("q5")))

    def test_graph_with_invalid_op(self):
        file_name = self.build_file_path("input/unsupported_op_types_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 6)
        self.assertEqual(automaton.get_nr_of_edges(), 7)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertIsNone(automaton.get_edge_operation("q1", "q2"))
        self.assertIsNone(automaton.get_edge_operation("q2", "q3"))
        self.assertIsNone(automaton.get_edge_operation("q3", "q1"))
        self.assertIsNone(automaton.get_edge_operation("q1", "q4"))
        self.assertIsNone(automaton.get_edge_operation("q4", "q5"))
        self.assertIsNone(automaton.get_edge_operation("q5", "q1"))

        self.assertEqual("edge1", str(automaton.get_edge_label("q0", "q1")))
        self.assertEqual("*0", str(automaton.get_edge_label("q1", "q2")))
        self.assertEqual("/20", str(automaton.get_edge_label("q2", "q3")))
        self.assertEqual("^1", str(automaton.get_edge_label("q3", "q1")))
        self.assertEqual("%0", str(automaton.get_edge_label("q1", "q4")))
        self.assertEqual("*20", str(automaton.get_edge_label("q4", "q5")))
        self.assertEqual("/1", str(automaton.get_edge_label("q5", "q1")))

        self.assertEqual("<=15.0", str(automaton.get_node_condition("q2")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q3")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q4")))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

        self.assertEqual("node1", str(automaton.get_node_label("q1")))
        self.assertEqual("node2", str(automaton.get_node_label("q2")))
        self.assertEqual("node3", str(automaton.get_node_label("q3")))
        self.assertEqual("node4", str(automaton.get_node_label("q4")))
        self.assertEqual("node5", str(automaton.get_node_label("q5")))

    def test_edge_with_conditional_label(self):
        file_name = self.build_file_path("input/conditional_edge_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 8)
        self.assertEqual(automaton.get_nr_of_edges(), 11)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertIsNone(automaton.get_edge_operation("q1", "_0"))
        self.assertIsNone(automaton.get_edge_operation("_0", "q2"))
        self.assertIsNone(automaton.get_edge_operation("q2", "_1"))
        self.assertIsNone(automaton.get_edge_operation("_1", "q3"))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q3", "q1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q4")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q4", "q5")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q5", "q1")))

        self.assertEqual("edge1", str(automaton.get_edge_label("q0", "q1")))
        self.assertEqual("edge2", str(automaton.get_edge_label("q1", "q2")))
        self.assertEqual("edge3", str(automaton.get_edge_label("q2", "q3")))
        self.assertEqual("edge5", str(automaton.get_edge_label("q3", "q1")))
        self.assertEqual("edge4", str(automaton.get_edge_label("q1", "q4")))
        self.assertEqual("edge6", str(automaton.get_edge_label("q4", "q5")))
        self.assertEqual("edge7", str(automaton.get_edge_label("q5", "q1")))

        self.assertEqual("<=10.0", str(automaton.get_node_condition("_0")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("_1")))
        self.assertEqual("<=15.0", str(automaton.get_node_condition("q2")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q3")))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q4")))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

        self.assertEqual("node1", str(automaton.get_node_label("q1")))
        self.assertEqual("node2", str(automaton.get_node_label("q2")))
        self.assertEqual("node3", str(automaton.get_node_label("q3")))
        self.assertEqual("node4", str(automaton.get_node_label("q4")))
        self.assertEqual("node5", str(automaton.get_node_label("q5")))

    def test_node_with_operational_label(self):
        file_name = self.build_file_path("input/operational_node_graph.dot")
        reader = DotReader(file_name)
        automaton = reader.create_automaton()

        self.assertEqual(automaton.get_nr_of_nodes(), 8)
        self.assertEqual(automaton.get_nr_of_edges(), 9)

        self.assertTrue(automaton.edge_exists("q1", "q2"))
        self.assertTrue(automaton.edge_exists("q2", "q3"))
        self.assertTrue(automaton.edge_exists("q3", "q1"))
        self.assertTrue(automaton.edge_exists("q1", "q4"))
        self.assertTrue(automaton.edge_exists("q4", "q5"))
        self.assertTrue(automaton.edge_exists("q5", "q1"))

        self.assertEqual("+15.0", str(automaton.get_edge_operation("q2", "_0")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q3", "_1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q2")))
        self.assertEqual("+20.0", str(automaton.get_edge_operation("q2", "q3")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q3", "q1")))
        self.assertEqual("+0.0", str(automaton.get_edge_operation("q1", "q4")))
        self.assertEqual("-20.0", str(automaton.get_edge_operation("q4", "q5")))
        self.assertEqual("+1.0", str(automaton.get_edge_operation("q5", "q1")))

        self.assertIsNone(automaton.get_edge_label("q2", "_0"))
        self.assertIsNone(automaton.get_edge_label("q3", "_1"))
        self.assertEqual("edge1", str(automaton.get_edge_label("q0", "q1")))
        self.assertEqual("edge2", str(automaton.get_edge_label("q1", "q2")))
        self.assertEqual("edge3", str(automaton.get_edge_label("q2", "q3")))
        self.assertEqual("edge5", str(automaton.get_edge_label("q3", "q1")))
        self.assertEqual("edge4", str(automaton.get_edge_label("q1", "q4")))
        self.assertEqual("edge6", str(automaton.get_edge_label("q4", "q5")))
        self.assertEqual("edge7", str(automaton.get_edge_label("q5", "q1")))

        self.assertIsNone(automaton.get_node_condition("q2"))
        self.assertIsNone(automaton.get_node_condition("q3"))
        self.assertIsNone(automaton.get_node_condition("_0"))
        self.assertIsNone(automaton.get_node_condition("_0"))
        self.assertEqual(">=20.0", str(automaton.get_node_condition("q4")))
        self.assertEqual("<=10.0", str(automaton.get_node_condition("q5")))

        self.assertEqual("node1", str(automaton.get_node_label("q1")))
        self.assertEqual("node2", str(automaton.get_node_label("q2")))
        self.assertEqual("node3", str(automaton.get_node_label("q3")))
        self.assertEqual("node4", str(automaton.get_node_label("q4")))
        self.assertEqual("node5", str(automaton.get_node_label("q5")))
