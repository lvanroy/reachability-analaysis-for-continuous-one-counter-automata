from Reach.Intervals import Intervals

from typing import Dict


class Reach:
    def __init__(self, node):
        self.node = node
        self.reachable_set: Dict[str, Intervals] = dict()

    def update_reach(self, state, interval):
        if state in self.reachable_set:
            self.reachable_set[state].union(interval)
        else:
            self.reachable_set[state] = interval

    def update_sup(self, state, sup):
        self.reachable_set[state].update_sup(sup)
        if sup == float('inf'):
            self.update_higher_bound_inclusive(state, False)

    def update_inf(self, state, inf):
        self.reachable_set[state].update_inf(inf)
        if inf == -float('inf'):
            self.update_lower_bound_inclusive(state, False)

    def update_lower_bound_inclusive(self, state, inclusive):
        self.reachable_set[state].update_lower_bound_inclusive(inclusive)

    def update_higher_bound_inclusive(self, state, inclusive):
        self.reachable_set[state].update_higher_bound_inclusive(inclusive)

    def rescale_reach(self, state, lower_bound, higher_bound):
        if state in self.reachable_set:
            self.reachable_set[state].rescale_reach(lower_bound, higher_bound)

    def ensure_reach_in_node_bounds(self, state):
        if self.node is not None:
            condition = self.node.get_condition()
            if condition is not None:
                operation = condition.get_operation()
                value = condition.get_value()
                if operation == "<=" and state in self.reachable_set:
                    intervals = self.reachable_set[state]
                    intervals.rescale_reach(float("-inf"), value)
                elif operation == ">=" and state in self.reachable_set:
                    intervals = self.reachable_set[state]
                    intervals.rescale_reach(value, float("+inf"))
                elif operation == "=" and state in self.reachable_set:
                    intervals = self.reachable_set[state]
                    intervals.rescale_reach(value, value)

    def remove_inconsistencies(self):
        for node in self.reachable_set:
            self.reachable_set[node].remove_inconsistencies()

    def get_preceding_nodes(self):
        return list(self.reachable_set.keys())

    def get_reachable_set(self, state):
        if state in self.reachable_set:
            return self.reachable_set[state]
        else:
            return None
