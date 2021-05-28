from typing import Dict, Tuple
from copy import deepcopy

from Reach.Reach import Reach
from Reach.Intervals import Intervals

from Automaton.Automaton import Automaton


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

        # keep track of the number of steps we have encountered
        self.n = 0

        # keep track of the encountered loops
        # the loops will be popped after accelerating
        self.loops = self.automaton.get_loops()

        # store whether or not we are finished evaluating
        # this is equivalent to no updated reaches during
        # an update automaton loop
        self.finished = False

        # track whether debug mode is on
        # if so, output additional info for each loop
        self.debug = debug

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
                self.add_interval(node, node, self.initial_value, True, self.initial_value, True)

    def initialise_intervals(self):
        for node in self.automaton.get_nodes():
            if self.automaton.is_invisible(node):
                continue
            self.intervals[node] = dict()

    def update_intervals(self):
        for node in self.reaches:
            for node2 in self.reaches:
                interval = self.reaches[node].get_reachable_set(node2)
                self.intervals[node][node2] = deepcopy(interval)

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

    # UPDATE THESE TO VERIFY WHETHER OR NOT THE CURRENT SUP/INF IS AN EXTENSION OF THE PREVIOUS
    # ADD THE RESULT IN THE CHECK_FOR_ACCELERATION FUNCTION
    # THINK ABOUT INTERVALS OR REACHES, PREFER INTERVALS AND SIMPLY VERIFY WHETHER OR NOT THE
    # CURRENT SUP/INF DOES NOT ALREADY EXCEED THE VALUE WE WISH TO ASSIGN, WHICH WOULD BE DUE TO
    # A DIFFERENT LOOP EVALUATION
    def is_ready_for_down_acceleration(self, loop):
        # track whether or not there is an actual step downwards
        # in case all infimums did not change this is not a downward acceleration
        decreased = False

        for i in range(len(loop)):
            prev_node = loop[i]
            current_node = loop[i % len(loop)]

            # analyse the current interval
            reach = self.reaches[current_node]
            current_interval = reach.get_reachable_set(prev_node)
            current_inf = current_interval.get_inf()
            current_inc = current_interval.is_inf_inclusive()

            # analyze the previous interval
            previous_interval = self.intervals[current_node][prev_node]
            previous_inf = previous_interval.get_inf()
            previous_inc = previous_interval.is_inf_inclusive()

            # if the infimum increased this is not accelerating downwards
            if previous_inf < current_inf:
                return False

            # detect decrease in the case that the infimum decreased
            if current_inf > previous_inf:
                decreased = True

            # detect decrease in the case that the infimum remained the same but became inclusive
            if current_inf == previous_inf and current_inc and not previous_inc:
                decreased = True

            # do nothing in the case that the infimum remained the exact same

        return decreased

    def is_ready_for_up_acceleration(self, loop):
        # track whether or not there is an actual step upwards
        # in case all suprema did not change this is not an upward acceleration
        increased = False

        for i in range(len(loop)):
            prev_node = loop[i]
            current_node = loop[i % len(loop)]

            # analyse the current interval
            reach = self.reaches[current_node]
            current_interval = reach.get_reachable_set(prev_node)
            current_sup = current_interval.get_sup()
            current_inc = current_interval.is_sup_inclusive()

            # analyze the previous interval
            previous_interval = self.intervals[current_node][prev_node]
            previous_sup = previous_interval.get_sup()
            previous_inc = previous_interval.is_sup_inclusive()

            # if the supremum decreased this is not accelerating upwards
            if current_sup < previous_sup:
                return False

            # detect increase in the case that the supremum decreased
            if current_sup > previous_sup:
                increased = True

            # detect increase in the case that the supremum remained the same but became inclusive
            if current_sup == previous_sup and current_inc and not previous_inc:
                increased = True

            # do nothing in the case that the supremum remained the exact same

        return increased

    def check_for_accelerations(self):
        for loop in self.loops:
            nodes = loop.get_nodes()
            upper_bound = None
            upper_node_bound = None
            upper_bound_node = None
            upper_bound_preceding_node = None
            lower_bound = None
            lower_node_bound = None
            lower_bound_node = None
            lower_bound_preceding_node = None

            # verify whether or not the entire chain has been discovered
            # track the min encountered value for upper bound - v
            # track the min encounter value for v - lower bound
            loop_discovered = True
            for i in range(len(nodes)):
                prev_node = nodes[i]
                current_node = nodes[i % len(nodes)]

                # if the reach set does not exist we have not fully evaluated
                # the loop yet and can therefore exit
                # in case the set exists but is empty, it means that we have
                # found a state that is at least for now not reachable, we
                # we can therefore exit
                if current_node in self.intervals:
                    intervals = self.intervals[current_node]
                    if prev_node in intervals:
                        reach_set = intervals[prev_node]
                    else:
                        loop_discovered = False
                        break
                else:
                    loop_discovered = False
                    break

                if reach_set is None or reach_set.is_empty():
                    loop_discovered = False
                    break

                current_node_obj = self.automaton.get_node(current_node)
                condition = current_node_obj.get_condition()

                # a condition was found
                # make sure that both bounds are correctly identified
                # in case of infinity there is no use for further evaluation
                # and we directly end the evaluation for that side here
                current_upper_bound = None
                current_lower_bound = None
                if condition is not None:
                    operation = condition.get_operation()
                    value = condition.get_value()
                    if operation == "<=":
                        current_upper_bound = value
                        if lower_bound is None:
                            lower_bound = -float('inf')
                            lower_bound_node = current_node
                            lower_bound_preceding_node = prev_node
                    elif operation == ">=":
                        current_lower_bound = value
                        if upper_bound is None:
                            upper_bound = float('inf')
                            upper_bound_node = current_node
                            upper_bound_preceding_node = prev_node
                    else:
                        current_upper_bound = value
                        current_lower_bound = value

                # no condition so the node bound is (-inf, inf)
                else:
                    if upper_bound is None:
                        upper_bound = float('inf')
                        upper_bound_node = current_node
                        upper_bound_preceding_node = prev_node
                    if lower_bound is None:
                        lower_bound = -float('inf')
                        lower_bound_node = current_node
                        lower_bound_preceding_node = prev_node
                    continue

                # get the current max value
                # if not inclusive we can simply subtract 0.1 as we work
                # under the assumption that all values are integers
                if current_upper_bound is not None:
                    if reach_set.is_sup_inclusive():
                        current_max_v = reach_set.get_sup()
                    else:
                        current_max_v = reach_set.get_sup() - 0.1
                    current_upper_dif = current_upper_bound - current_max_v
                    if upper_bound is None or current_upper_dif < upper_bound:
                        upper_bound = current_upper_dif
                        upper_node_bound = current_upper_bound
                        upper_bound_node = current_node
                        upper_bound_preceding_node = prev_node

                # get the current min value
                # if not inclusive we can simply subtract 0.1 as we work
                # under the assumption that all values are integers
                if current_lower_bound is not None:
                    if reach_set.is_inf_inclusive():
                        current_min_v = reach_set.get_inf()
                    else:
                        current_min_v = reach_set.get_inf() + 0.1
                    current_lower_dif = current_min_v - current_lower_bound
                    if lower_bound is None or current_lower_dif < lower_bound:
                        lower_bound = current_lower_dif
                        lower_node_bound = current_lower_bound
                        lower_bound_node = current_node
                        lower_bound_preceding_node = prev_node

            # if the loop was not ready for acceleration, simply continue
            if not loop_discovered:
                continue

            # accelerate the upper bound
            if self.is_ready_for_up_acceleration(nodes):
                reach = self.reaches[upper_bound_node]
                if upper_bound == float('inf'):
                    reach.update_sup(upper_bound_preceding_node, float('inf'))
                    reach.update_higher_bound_inclusive(upper_bound_preceding_node, False)
                else:
                    reach.update_sup(upper_bound_preceding_node, upper_node_bound)
                    reach.update_higher_bound_inclusive(upper_bound_preceding_node, True)

            # accelerate the lower bound
            if self.is_ready_for_down_acceleration(nodes):
                reach = self.reaches[lower_bound_node]
                if lower_bound == -float('inf'):
                    reach.update_inf(lower_bound_preceding_node, -float('inf'))
                    reach.update_lower_bound_inclusive(lower_bound_preceding_node, False)
                else:
                    reach.update_inf(lower_bound_preceding_node, lower_node_bound)
                    reach.update_lower_bound_inclusive(lower_bound_preceding_node, True)

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

        self.check_for_accelerations()

        if self.debug:
            print(self)

        self.verify_end_condition()
        if self.finished:
            return

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
                        new_interval = deepcopy(sub_interval)

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
