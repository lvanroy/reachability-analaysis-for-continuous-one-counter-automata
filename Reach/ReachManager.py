from typing import Dict, Tuple
from copy import deepcopy

from Reach.Reach import Reach
from Reach.Intervals import Intervals

from Automaton.Automaton import Automaton
from Automaton.LoopFinder import Loop


class ReachManager:
    def __init__(self, automaton, debug=False):
        self.automaton: Automaton = automaton

        self.upper_bound = automaton.get_upper_bound()
        self.lower_bound = automaton.get_lower_bound()
        self.initial_value = automaton.get_initial_value()

        # the reaches dict tracks the reachability data for each state
        #   this data will always be up to date and will be directly updated during the post
        self.reaches: Dict[str, Reach] = dict()

        # the intervals dict will track the reachability data at the start of each post update
        #   the dict will be updated at the end of every post operation, rather than during
        self.intervals: Dict[str, Dict[str, Intervals]] = dict()

        # for each node we will track the number of consecutive times in which
        # the interval expanded. It is tracked for each proceeding state of each state
        #   interval expanded or remained the same size -> +1
        #   interval decreased in size -> 0
        self.up_expansions: Dict[Loop, int] = dict()
        self.down_expansions: Dict[Loop, int] = dict()

        # keep track of the number of steps we have encountered
        self.n = 0

        # store whether or not we are finished evaluating
        # this is equivalent to no updated reaches during
        # an update automaton loop
        self.finished = False

        # track whether debug mode is on
        # if so, output additional info for each loop
        self.debug = False

        self.initialise_intervals()
        self.initialise_reaches()
        self.initialize_expansions()
        self.update_intervals()

    def initialise_reaches(self):
        nodes = self.automaton.get_nodes()
        for node in nodes:
            if self.automaton.is_invisible(node):
                continue
            self.add_state(node)
            if self.automaton.is_initial(node):
                self.add_interval(node, node, self.initial_value, True, self.initial_value, True)

    def initialise_intervals(self):
        for node in self.automaton.get_nodes():
            if self.automaton.is_invisible(node):
                continue
            self.intervals[node] = dict()

    def initialize_expansions(self):
        for loop in self.automaton.get_loops():
            self.up_expansions[loop] = 0
            self.down_expansions[loop] = 0

    def update_intervals(self):
        for node in self.reaches:
            for node2 in self.reaches:
                interval = self.reaches[node].get_reachable_set(node2)
                self.intervals[node][node2] = deepcopy(interval)

    def update_expansions(self):
        for loop in self.automaton.get_loops():
            expanded = True
            expanded_up = True
            expanded_down = True
            loop_nodes = loop.get_nodes()
            for i in range(len(loop_nodes)):
                current_node = loop_nodes[i]
                prev_node = loop_nodes[i-1]
                old_interval = self.intervals[current_node][prev_node]
                new_interval = self.reaches[current_node].get_reachable_set(prev_node)
                if new_interval is None:
                    expanded = False
                    break
                if old_interval is None:
                    continue
                is_expansion = new_interval.is_expansion_of(old_interval)
                if not is_expansion:
                    expanded = False
                    break
                if old_interval.is_empty():
                    continue
                if new_interval.is_empty():
                    expanded = False
                    break
                if new_interval.get_inf() > old_interval.get_inf():
                    expanded_down = False
                if new_interval.get_inf() < old_interval.get_inf():
                    loop.register_downwards_expansion()
                if new_interval.get_sup() < old_interval.get_sup():
                    expanded_up = False
                if new_interval.get_sup() > old_interval.get_sup():
                    loop.register_upwards_expansion()

            if expanded:
                if expanded_down:
                    self.down_expansions[loop] += 1
                if expanded_up:
                    self.up_expansions[loop] += 1
            else:
                self.down_expansions[loop] = 0
                self.up_expansions[loop] = 0

    def add_state(self, state):
        nodes = self.automaton.get_nodes()
        if state in nodes:
            node = self.automaton.get_nodes()[state]
        else:
            node = None

        self.reaches[state] = Reach(node)

    def add_interval(self, state, origin, low, inc_low, high, inc_high):
        if low > self.upper_bound or high < self.lower_bound:
            return

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

    def get_down_expansions(self) -> Dict[Loop, int]:
        return self.down_expansions

    def get_up_expansions(self) -> Dict[Loop, int]:
        return self.up_expansions

    def is_ready_for_down_acceleration(self, loop):
        nr_of_nodes = len(self.automaton.get_nodes())
        bound = nr_of_nodes * (4 * nr_of_nodes + 4)
        return self.down_expansions[loop] >= bound

    def is_ready_for_up_acceleration(self, loop):
        nr_of_nodes = len(self.automaton.get_nodes())
        bound = nr_of_nodes * (4 * nr_of_nodes + 4)
        return self.up_expansions[loop] >= bound

    def accelerate_up(self, loop):
        if not loop.has_upwards_expanded():
            return

        max_bound = loop.get_max_bound()
        max_bounded_node = loop.get_max_bounded_node()
        max_preceding_node = loop.get_max_preceding_node()

        if max_bound is None:
            start = loop.get_nodes()[-1]
            end = loop.get_nodes()[0]
            reach = self.reaches[start]
            reach.update_sup(end, float('inf'))
            reach.rescale_reach(end, self.lower_bound, self.upper_bound)

        else:
            reach = self.reaches[max_bounded_node]
            reach.update_sup(max_preceding_node, max_bound)
            reach.rescale_reach(max_preceding_node, self.lower_bound, self.upper_bound)

    def accelerate_down(self, loop):
        if not loop.has_downwards_expanded():
            return

        min_bound = loop.get_max_bound()
        min_bounded_node = loop.get_max_bounded_node()
        min_preceding_node = loop.get_max_preceding_node()

        if min_bound is None:
            start = loop.get_nodes()[-1]
            end = loop.get_nodes()[0]
            reach = self.reaches[start]
            reach.update_inf(end, -float('inf'))
            reach.rescale_reach(end, self.lower_bound, self.upper_bound)

        else:
            reach = self.reaches[min_bounded_node]
            reach.update_inf(min_preceding_node, min_bound)
            reach.rescale_reach(min_preceding_node, self.lower_bound, self.upper_bound)

    def verify_end_condition(self):
        for node in self.reaches:
            reach = self.reaches[node]
            for origin in self.automaton.get_nodes():
                reachable_set = reach.get_reachable_set(origin)

                # this means implies that there are no reaches from this origin node
                if reachable_set is None:
                    continue

                previous_set = self.intervals[node][origin]

                if reachable_set is None:
                    continue

                if previous_set is None:
                    return

                if not reachable_set.equals(previous_set):
                    return

        self.finished = True

    def is_finished(self):
        return self.finished

    # For each state in the Automaton
    #   Update all their reaches
    def update_automaton(self):
        for state in self.reaches.keys():
            if self.automaton.is_invisible(state):
                continue
            self.update_state(state)

        for loop in self.automaton.get_loops():
            if self.is_ready_for_down_acceleration(loop):
                self.accelerate_down(loop)
            if self.is_ready_for_up_acceleration(loop):
                self.accelerate_up(loop)

        if self.debug:
            print(self)

        self.verify_end_condition()
        if self.finished:
            return

        self.update_expansions()
        self.update_intervals()
        self.n += 1

    def update_state(self, q):
        proceeding_edges = self.automaton.get_proceeding_edges(q)

        for p in proceeding_edges:
            for edge in proceeding_edges[p]:
                if self.automaton.is_invisible(p):
                    continue

                for sub_interval in self.intervals[p].values():
                    if sub_interval is None:
                        continue

                    if sub_interval.is_empty():
                        continue

                    op = edge.get_operation()
                    if op is not None:
                        z = edge.get_operation().get_value()
                    else:
                        z = 0

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
                    self.reaches[q].remove_inconsistencies()

    def is_reachable(self, node):
        reach = self.reaches[node]

        for node in self.automaton.get_nodes():
            reachable_set = reach.get_reachable_set(node)
            if reachable_set is None:
                continue

            if not reachable_set.is_empty():
                return True

        return False

    def set_debug(self, debug):
        self.debug = debug

    def __str__(self):
        result = ""
        for node in self.automaton.get_nodes():
            if self.automaton.is_invisible(node):
                continue
            result += "For node {}:\n".format(node)
            reach = self.intervals[node]
            for preceding in reach:
                if reach[preceding] is not None:
                    result += "\t{}: {}\n".format(preceding, reach[preceding])
        return result
