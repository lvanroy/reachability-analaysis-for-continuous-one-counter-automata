from Reach.Reach import Reach
from Reach.Intervals import Intervals

from automaton.Automaton import Automaton

from typing import Dict


class ReachManager:
    def __init__(self, automaton):
        self.automaton: Automaton = automaton

        self.upper_bound = automaton.get_upper_bound()
        self.lower_bound = automaton.get_lower_bound()

        # the reaches dict tracks the reachability data for each state
        #   this data will always be up to date and will be directly updated during the post
        self.reaches: Dict[str, Reach] = dict()

        # the intervals dict will track the reachability data at the start of each post update
        #   the dict will be updated at the end of every post operation, rather than during
        self.intervals: Dict[str, Dict[str, Intervals]] = dict()

        self.initialise_intervals()
        self.initialise_reaches()
        self.update_intervals()

    def initialise_reaches(self):
        nodes = self.automaton.get_nodes()
        for node in nodes:
            if self.automaton.is_invisible(node):
                continue
            self.add_state(node)
            if self.automaton.is_initial(node):
                self.add_interval(node, node, 0, True, 0, True)

    def initialise_intervals(self):
        for node in self.automaton.get_nodes():
            self.intervals[node] = dict()

    def update_intervals(self):
        for node in self.reaches:
            for node2 in self.reaches:
                interval = self.reaches[node].get_reachable_set(node2)
                self.intervals[node][node2] = interval

    def add_state(self, state):
        nodes = self.automaton.get_nodes()
        if state in nodes:
            node = self.automaton.get_nodes()[state]
        else:
            node = None

        self.reaches[state] = Reach(node)

    def add_interval(self, state, origin, low, inc_low, high, inc_high):
        high = min(self.upper_bound, high)
        high = max(self.lower_bound, high)

        low = max(self.automaton.lower_bound, low)
        low = min(self.automaton.upper_bound, low)

        interval = Intervals(low, inc_low, high, inc_high)
        self.reaches[state].update_reach(origin, interval)

    def get_reach(self, state):
        if state in self.reaches:
            return self.reaches[state]
        return None

    def get_interval(self, state, origin):
        if state in self.reaches:
            return self.reaches[state].get_reachable_set(origin)
        else:
            return None

    # For each state in the automaton
    #   Update all their reaches
    def post_automaton(self):
        for state in self.reaches.keys():
            if self.automaton.is_invisible(state):
                continue
            self.post_state(state)

        self.update_intervals()

    def post_state(self, q):
        proceeding_edges = self.automaton.get_proceeding_edges(q)

        for p in proceeding_edges:
            for edge in proceeding_edges[p]:
                for sub_interval in self.intervals[p].values():
                    if sub_interval is None:
                        continue

                    z = edge.get_operation().get_value()
                    if z > 0:
                        new_interval = Intervals(0, False, z, True)
                        new_interval.add(sub_interval)
                    elif z < 0:
                        new_interval = Intervals(z, True, 0, False)
                        new_interval.add(sub_interval)
                    else:
                        new_interval = sub_interval

                    self.reaches[q].update_reach(p, new_interval)
                    self.reaches[q].rescale_reach(p, self.lower_bound, self.upper_bound)
                    self.reaches[q].ensure_reach_in_node_bounds(p)
