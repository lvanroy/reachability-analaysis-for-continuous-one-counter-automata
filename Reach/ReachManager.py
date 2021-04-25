from Reach.Reach import Reach
from automaton.Automaton import Automaton

from typing import Dict


class ReachManager:
    def __init__(self, automaton):
        self.automaton: Automaton = automaton
        self.reaches: Dict[str, Reach] = dict()

        self.initialise_reaches()

    def initialise_reaches(self):
        nodes = self.automaton.get_nodes()
        for node in nodes:
            if self.automaton.is_invisible(node):
                continue
            if self.automaton.is_initial(node):
                self.add_state(node, 0)
                continue
            self.add_state(node)

    def add_state(self, state, val=None):
        reach = Reach()

        if val is not None:
            reach.update_reach(val)

        self.reaches[state] = reach

    def get_reach(self, state):
        if state in self.reaches:
            return self.reaches[state]
        return None

    def post(self, q):
        updated_reach = self.reaches[q].get_reachable_set()

        edges = self.automaton.get_edges()
        outgoing_edges = edges[q]

        for p in outgoing_edges:
            edge = outgoing_edges[p]
            z = edge.get_operation().get_value()

            target_reach = self.reaches[p].get_reachable_set()

