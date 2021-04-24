import unittest

from Reach.ReachManager import ReachManager
from automaton.Automaton import Automaton


class TestNewReachConfiguration(unittest.TestCase):
    def test_no_node_configuration(self):
        manager = ReachManager(Automaton("test"))

        self.assertIsNone(manager.get_reach("q0"))

    def test_one_node_configuration(self):
        manager = ReachManager(Automaton("test"))

        manager.add_state("q0", 0)

        reach = manager.get_reach("q0")
        self.assertIsNotNone(reach)
        self.assertEqual([0], reach.get_reachable_set())

    def test_multi_node_configuration(self):
        manager = ReachManager(Automaton("test"))

        manager.add_state("q0", 0)
        manager.add_state("q1")
        manager.add_state("q2")

        reach = manager.get_reach("q0")
        self.assertIsNotNone(reach)
        self.assertEqual([0], reach.get_reachable_set())

        reach = manager.get_reach("q1")
        self.assertIsNotNone(reach)
        self.assertEqual(list(), reach.get_reachable_set())

        reach = manager.get_reach("q2")
        self.assertIsNotNone(reach)
        self.assertEqual(list(), reach.get_reachable_set())

    def test_automaton_configuration(self):
        automaton = Automaton("test")

        automaton\
            .create_new_node("qi")\
            .create_new_node("q0")\
            .create_new_node("q1")\
            .create_new_node("q2")\
            .create_new_edge("q0", "q1")\
            .create_new_edge("q1", "q2")\
            .create_new_edge("qi", "q0")

        automaton.set_node_invisible("qi")

        automaton.find_initial_node()

        manager = ReachManager(automaton)

        reach = manager.get_reach("q0")
        self.assertIsNotNone(reach)
        self.assertEqual([0], reach.get_reachable_set())

        reach = manager.get_reach("q1")
        self.assertIsNotNone(reach)
        self.assertEqual(list(), reach.get_reachable_set())

        reach = manager.get_reach("q2")
        self.assertIsNotNone(reach)
        self.assertEqual(list(), reach.get_reachable_set())




