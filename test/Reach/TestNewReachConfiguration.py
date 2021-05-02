import unittest

from Reach.ReachManager import ReachManager

from Automaton.Automaton import Automaton


class TestNewReachConfiguration(unittest.TestCase):
    def test_no_node_configuration(self):
        manager = ReachManager(Automaton("test", 0, 10))

        self.assertIsNone(manager.get_reach("q0"))

    def test_one_node_configuration(self):
        manager = ReachManager(Automaton("test", 0, 10))

        manager.add_state("q0")

        manager.add_interval("q0", "q0", 0, True, 0, True)

        reach = manager.get_reach("q0")
        interval = reach.get_reachable_set("q0")
        self.assertIsNotNone(reach)
        self.assertIsNotNone(interval)
        self.assertEqual("[0, 0]", str(interval))

    def test_multi_node_configuration(self):
        manager = ReachManager(Automaton("test", 0, 10))

        manager.add_state("q0")
        manager.add_state("q1")
        manager.add_state("q2")

        manager.add_interval("q0", "q0", 0, True, 0, True)

        reach = manager.get_reach("q0")
        interval = reach.get_reachable_set("q0")
        self.assertIsNotNone(reach)
        self.assertIsNotNone(interval)
        self.assertEqual("[0, 0]", str(interval))

        reach = manager.get_reach("q1")
        interval = reach.get_reachable_set("q1")
        self.assertIsNotNone(reach)
        self.assertIsNone(interval)

        reach = manager.get_reach("q2")
        interval = reach.get_reachable_set("q2")
        self.assertIsNotNone(reach)
        self.assertIsNone(interval)

    def test_automaton_configuration(self):
        automaton = Automaton("test", 0, 10)

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
        interval = reach.get_reachable_set("q0")
        self.assertIsNotNone(reach)
        self.assertIsNotNone(interval)
        self.assertEqual("[0, 0]", str(interval))

        reach = manager.get_reach("q1")
        interval = reach.get_reachable_set("q1")
        self.assertIsNotNone(reach)
        self.assertIsNone(interval)

        reach = manager.get_reach("q2")
        interval = reach.get_reachable_set("q2")
        self.assertIsNotNone(reach)
        self.assertIsNone(interval)

    def test_interval_bounds(self):
        automaton = Automaton("test", 0, 10)

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

        manager.add_interval("q1", "q0", 0, True, 20, True)

        reach = manager.get_reach("q0")
        interval = reach.get_reachable_set("q0")
        self.assertIsNotNone(reach)
        self.assertIsNotNone(interval)
        self.assertEqual("[0, 0]", str(interval))

        reach = manager.get_reach("q1")
        interval = reach.get_reachable_set("q0")
        self.assertIsNotNone(reach)
        self.assertIsNotNone(interval)
        self.assertEqual("[0, 10]", str(interval))

        reach = manager.get_reach("q2")
        interval = reach.get_reachable_set("q2")
        self.assertIsNotNone(reach)
        self.assertIsNone(interval)
