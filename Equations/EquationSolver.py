from z3 import *
from typing import List, Dict
from Automaton.Edge import Edge

import operator


class EquationSolver:
    def __init__(self, automaton):
        self.automaton = automaton
        print(self.automaton)
        self.s = Solver()
        self.s.set("timeout", 300000)
        self.auxiliary_counter = 0
        self.nodes = list(self.automaton.get_visible_nodes().keys())

        # store all the node conditions defined within the automaton
        # this list will be used to trace the bounds implied by the
        # different nodes. Each transition will have a corresponding
        # condition representing the condition of its end node
        # this will be stored in a consecutive list in pairs of two
        # where the first entry will represent the constraint
        # the second entry will represent the condition
        # 0 -> >=, 1 -> <=, 2 -> =, 3 -> no condition
        #   c0, v0, c1, v1, c2, v2, ...
        self.conditions: List[int] = list()
        self.selected_conditions: List[int] = list()

        # store all the edges defined within the automaton
        # this list will be used to provide the options
        # from which our transitions need to pick
        # every three consecutive entries form one edge
        #   s0, z0, e0, s1, z1, e1, ...
        self.edges = list()
        self.edge_mapping: Dict[Edge, int] = dict()

        # the transition objects created for our formula
        # each of these transitions will match one edge
        # every three consecutive entries form one transition
        #   s0, z0, e0, s1, z1, e1, ...
        self.transitions: List[ArithRef] = list()

        # the intervals used within the different stages. Each four
        # consecutive entries will match one sub interval for one
        # specific node where the first interval matches node 0
        # each node has x sub intervals with
        #       x = 4 |Q| + 4
        #   b0, t0, ⊥0, ⊤0, b1, t1, ⊥1, ⊤1, ...
        self.intervals: List[ArithRef] = list()
        self.y: List[ArithRef] = list()

        # keep track of the variables that are found throughout the evaluation
        # these will get values assigned to them and can be retrieved
        # afterwards by their reference
        self.vars: Dict[str, ArithRef] = dict()

        # keep track of the found parameters
        # this is so that we reuse the same variable every time
        # we refer to this parameter, rather than creating a new one
        self.parameters: Dict[str, IntVal] = dict()

        # track the number of intervals per node
        self.nr_of_intervals = 4 * len(self.nodes) + 4

        # track the transition that was used to achieve an interval
        # to prevent reevaluating the same interval over and over
        self.used_edges = list()

        # track if a node contains a not empty sub interval
        self.reachable = list()

    def analyse(self):
        self.build_transitions()
        self.build_node_conditions()
        self.build_intervals()
        self.analyse_loops()
        self.add_successor_condition()
        self.add_reachability_condition()

        print(self.nodes)

        reachable_nodes = list()

        # start solving for each of the intervals
        unchecked_nodes = self.nodes.copy()
        while unchecked_nodes:
            cur_node = unchecked_nodes.pop(0)
            cur_index = self.nodes.index(cur_node)
            self.s.push()
            self.add_final_condition(cur_index)
            self.solve()
            if self.s.check() == sat:
                reachable_nodes.append(cur_node)
                m = self.s.model()
                for i in range(len(self.reachable)):
                    if m[self.reachable[i]].as_long():
                        node = self.nodes[i]
                        if node in unchecked_nodes:
                            reachable_nodes.append(node)
                            unchecked_nodes.remove(node)
            self.s.pop()

        print(reachable_nodes)

    # ensure that the node under test is not empty
    def add_final_condition(self, cur_node):
        base_index = cur_node * self.nr_of_intervals
        condition = list()
        for i in range(self.nr_of_intervals):
            condition.append(self.used_edges[base_index + i] != -2)
        self.s.add(Or(condition))

    # fetch all edges from the automaton
    # convert each edge to [from, op, end] format
    # from and end are mapped to integers where
    # each integer represents a node
    def build_transitions(self):
        for start in self.nodes:
            for end in self.automaton.get_outgoing_edges(start):
                edge = self.automaton.get_edge(start, end)
                start_index = self.get_index_of_node(edge.get_start())
                end_index = self.get_index_of_node(edge.get_end())
                if edge.get_operation() is not None:
                    operation = edge.get_operation().get_value()
                else:
                    operation = 0

                transition = list()
                transition.append(start_index)
                transition.append(operation)
                transition.append(end_index)
                index = int(len(self.edges) / 3)
                self.edge_mapping[edge] = index
                self.edges += transition

    # find which edges are part of loops that do are pure add/sub
    def analyse_loops(self):
        bound_upper_loops = list()
        bound_lower_loops = list()

        # keep track of which edges are part of which type of loop
        lower_bound_edges = list()
        upper_bound_edges = list()
        lower_unbound_edges = list()
        upper_unbound_edges = list()
        for loop in self.automaton.get_loops():
            nodes = loop.get_nodes()
            is_bound_lower = True
            is_bound_upper = True
            for i in range(len(nodes)):
                node = nodes[i]
                next_node = nodes[(i + 1) % len(nodes)]

                edge = self.automaton.get_outgoing_edges(node)[next_node]
                index = self.edge_mapping[edge]

                if loop.has_add() and edge not in upper_unbound_edges:
                    upper_unbound_edges.append(index)
                    if index in upper_bound_edges:
                        upper_bound_edges.remove(index)
                    is_bound_upper = False

                if not loop.has_add() and \
                        index not in upper_unbound_edges and \
                        index not in upper_bound_edges:
                    upper_bound_edges.append(index)

                if loop.has_sub() and index not in lower_unbound_edges:
                    lower_unbound_edges.append(index)
                    if index in lower_bound_edges:
                        lower_bound_edges.remove(index)
                    is_bound_lower = False

                if not loop.has_sub() and \
                        index not in lower_unbound_edges and \
                        index not in lower_bound_edges:
                    lower_bound_edges.append(index)

            if is_bound_upper:
                bound_upper_loops.append(loop)
            if is_bound_lower:
                bound_lower_loops.append(loop)

        # generate an "is inf" condition for all nodes
        is_inf = dict()
        is_bounded = dict()

        for loop in bound_lower_loops:
            self.generate_loop_conditions(is_inf, is_bounded, loop, 0)
            self.apply_loop_conditions(is_inf, is_bounded, loop, 0)

        for loop in bound_upper_loops:
            self.generate_loop_conditions(is_inf, is_bounded, loop, 1)
            self.apply_loop_conditions(is_inf, is_bounded, loop, 1)

    # generate the sub conditions for the different loops
    # these sub conditions will be used to specify one big constraint
    def generate_loop_conditions(self, is_inf, is_bounded, loop, offset):
        for node in loop.get_nodes():
            node = self.nodes.index(node)
            if node in is_inf:
                continue

            is_inf[node] = list()
            is_bounded[node] = dict()

            # get the index of the start of the first sub interval
            base_sub_index = node * self.nr_of_intervals * 4

            # get the index of the start of the first sub intervals' edge
            base_edge_index = node * self.nr_of_intervals

            for sub in range(self.nr_of_intervals):
                is_bounded[node][sub] = list()

                # get the incl val of the start of the cur sub interval
                incl_bound_index = base_sub_index + sub * 4 + 2 + offset
                incl_bound_val = self.intervals[incl_bound_index]

                # get the val of the edge linked to the cur sub interval
                edge_index = base_edge_index + sub
                edge_val = self.used_edges[edge_index]

                # check if this sub interval has an inf bound
                is_inf[node].append(
                    And(
                        incl_bound_val == 2,
                        edge_val != -2
                    )
                )

                # get the bound val of this sub interval
                low_index = base_sub_index + sub * 4 + offset
                bound_val = self.intervals[low_index]

                # iterate over all other sub intervals in the cur node
                for sub2 in range(self.nr_of_intervals):
                    if sub == sub2:
                        continue

                    # get the bound val of the second sub interval
                    low_index2 = base_sub_index + sub2 * 4 + offset
                    bound_val2 = self.intervals[low_index2]

                    # get the linked edge of this second sub interval
                    edge_index2 = base_edge_index + sub2
                    edge_val2 = self.used_edges[edge_index2]

                    # check is this node is bounded by the second interval
                    is_bounded[node][sub].append(
                        And(
                            bound_val >= bound_val2,
                            edge_val2 != -2
                        )
                    )

    def apply_loop_conditions(self, is_inf, is_bounded, loop, offset):
        condition = list()
        not_taken = list()
        nodes = loop.get_nodes()
        indexes = [self.nodes.index(node) for node in nodes]

        # for all sub intervals of all nodes part of this loop
        # if edge equals any edge part of this loop
        # A or B must hold
        for i in range(len(indexes)):
            index = indexes[i]
            or_condition = list()

            # get the current node under eval
            node = self.nodes[index]
            print(node)
            base_sub_index = index * self.nr_of_intervals * 4
            base_edge_index = index * self.nr_of_intervals

            # get the prev node in the loop
            prev_index = indexes[(i - 1) % len(indexes)]
            print(prev_index)
            prev_node = self.nodes[prev_index]

            # get the edge associated with this node sequence
            edge = self.automaton.get_outgoing_edges(prev_node)[node]
            print(edge)
            edge_index = self.edge_mapping[edge]

            # consider the case in which the loop is simply not taken
            no_loop_taken = list()
            for j in range(self.nr_of_intervals):
                edge_val = self.used_edges[base_edge_index + j]
                no_loop_taken.append(edge_val != edge_index)
            not_taken += no_loop_taken

            # consider the cases in which the loop is taken
            for j in range(self.nr_of_intervals):
                loop_taken = list()
                loop_condition = list()

                # ensure that we do take the edge
                edge_val = self.used_edges[base_edge_index + j]
                loop_taken.append(edge_val == edge_index)

                # get the subset of inf conditions that apply here
                inf_condition = is_inf[index]
                inf_exists = [x for y, x in enumerate(inf_condition)
                              if y != j]

                # apply the inf condition
                #   if any of the other sub intervals reaches inf
                #   this interval must reach infinity
                sub_index = base_sub_index + j * 4
                bound_val = self.intervals[sub_index + offset]
                bound_incl_val = self.intervals[sub_index + 2 + offset]
                loop_condition.append(
                    And(
                        Or(inf_exists),
                        bound_val == 0,
                        bound_incl_val == 2
                    )
                )

                # apply the is bounded condition which will ensure that
                # our bound is higher/lower than the current min/max
                loop_condition.append(
                    Or(is_bounded[index][j])
                )
                loop_taken.append(Or(loop_condition))
                or_condition.append(And(loop_taken))

            # the above conditions must hold for one of the nodes of the loop
            condition.append(Or(or_condition))

        # check if all edges part of this loop are effectively taken
        # if not it makes no sense to apply bounds
        condition.append(And(not_taken))
        self.s.add(Or(condition))

    # store all node conditions
    def build_node_conditions(self):
        for i in range(len(self.nodes)):
            node = self.nodes[i]
            end_condition = self.automaton.get_node_condition(node)
            condition = list()
            if end_condition is None:
                condition.append(3)
                condition.append(0)
            else:
                operation = end_condition.get_operation()
                if operation == ">=":
                    condition.append(0)
                elif operation == "<=":
                    condition.append(1)
                else:
                    condition.append(2)
                condition.append(end_condition.get_value())
            self.conditions += condition

    def build_intervals(self):
        # initialise all intervals
        for n in range(len(self.nodes)):
            for s in range(self.nr_of_intervals):
                self.intervals += self.generate_interval(n, s)
                self.used_edges.append(Int('t_{}_{}'.format(n, s)))

        # initialise the reachability values tracking whether or not
        # the corresponding node is reachable
        for n in range(len(self.nodes)):
            self.reachable.append(Int('r_{}'.format(n)))

    # ensure that for the sub intervals of all nodes they are
    # a successor of a preceding node
    def add_successor_condition(self):
        # for all nodes in the automaton
        for node in range(len(self.nodes)):
            base_end = node * self.nr_of_intervals * 4
            used_edge_base = node * self.nr_of_intervals

            # get the condition of the current node
            cond_base_index = int(node * 2)
            cond_type = self.conditions[cond_base_index]
            cond_value = self.conditions[cond_base_index + 1]

            print("{} {}".format(cond_type, cond_value))

            # track the conditions for each of the sub intervals
            or_conditions = dict()
            for i in range(self.nr_of_intervals):
                or_conditions[i] = list()

            # check if the current node is the initial node
            if self.nodes[node] == self.automaton.get_initial_node():
                vec_name = 'y{}'.format(self.auxiliary_counter)
                self.auxiliary_counter += 1
                y = IntVector(vec_name, 4)

                # initialise the first sub interval of the initial node
                interval = self.intervals[base_end: base_end + 4]
                init_val = self.automaton.get_initial_value()
                cond = list()
                cond += self.assign(interval, init_val, init_val, 1, 1)
                cond.append(And(self.is_in_bounds(interval, interval,
                                                  (cond_type, cond_value), y)))
                cond.append(self.used_edges[0] == -1)
                or_conditions[0].append(And(cond))

            # go over all the edges that end in the current node
            for edge in range(0, len(self.edges), 3):
                start = self.edges[edge]
                op = self.edges[edge + 1]
                end = self.edges[edge + 2]

                # if the edge does not end in the current node continue
                if end != node:
                    continue

                print("{} {} {}".format(start, op, end))

                vec_name = 'y{}'.format(self.auxiliary_counter)
                self.auxiliary_counter += 1
                y = IntVector(vec_name, 4)
                self.y += y

                vec_name2 = 'y{}'.format(self.auxiliary_counter)
                self.auxiliary_counter += 1
                y2 = IntVector(vec_name2, 4)
                self.y += y2

                base_start = start * self.nr_of_intervals * 4

                # ensure that there is at least one edge for which
                # there is a preceding interval from which the current
                # interval can be generated
                for new_int in range(self.nr_of_intervals):

                    if node == 0 and new_int == 0:
                        continue

                    unique_update = list()

                    # get the interval of the end node
                    end_index = base_end + new_int * 4
                    end_interval = self.intervals[end_index: end_index + 4]

                    # ensure that we store which edge was used to generate
                    # the linked interval
                    used_edge_index = used_edge_base + new_int
                    used_edge_var = self.used_edges[used_edge_index]
                    edge_cond = used_edge_var == edge / 3
                    unique_update.append(edge_cond)

                    # ensure that only one interval results from this edge
                    for other_int in range(0, new_int):
                        past_edge_index = used_edge_base + other_int
                        past_edge_var = self.used_edges[past_edge_index]
                        edge_not_used = past_edge_var != used_edge_var
                        unique_update.append(edge_not_used)

                    for prev_int in range(self.nr_of_intervals):
                        # get the interval of the start node
                        start_index = base_start + prev_int * 4
                        start_interval = self.intervals[start_index:
                                                        start_index + 4]

                        # generate the successor condition
                        update = self.update_interval(start_interval,
                                                      op,
                                                      end_interval,
                                                      (cond_type, cond_value),
                                                      y, y2)

                        unique_update.append(update)

                        # allow a way out in case the current interval is empty
                        # if not every interval will be forced to be filled
                        empty_cond = And(*self.is_empty(end_interval[0],
                                                        end_interval[1],
                                                        end_interval[2],
                                                        end_interval[3]),
                                         used_edge_var == -2)

                        final_cond = If(And(unique_update), True, empty_cond)
                        unique_update.pop(-1)

                        or_conditions[new_int].append(final_cond)

                print("{} -> {} -> {}".format(start, op, end))

            for key in or_conditions.keys():
                condition = or_conditions[key]
                if condition:
                    # print(len(or_condition))
                    self.s.add(Or(condition))
                else:
                    end_index = base_end + key * 4
                    end_interval = self.intervals[end_index: end_index + 4]
                    used_edge_index = used_edge_base + key
                    used_edge_var = self.used_edges[used_edge_index]
                    empty_cond = And(*self.is_empty(end_interval[0],
                                                    end_interval[1],
                                                    end_interval[2],
                                                    end_interval[3]),
                                     used_edge_var == -2)
                    self.s.add(empty_cond)

    def add_reachability_condition(self):
        for n in range(len(self.nodes)):
            or_conditions = list()
            base_index = n * self.nr_of_intervals * 4

            for i in range(self.nr_of_intervals):
                index = base_index + i * 4
                interval = self.intervals[index: index + 4]
                cond = self.is_not_empty(interval[0], interval[1],
                                         interval[2], interval[3])
                or_conditions.append(Or(cond))

            reachable = self.reachable[n]
            cond = If(Or(or_conditions), reachable == 1, reachable == 0)
            self.s.add(cond)

    def update_interval(self, start, z, end, node_cond, y, y2):
        update_condition = list()

        condition = Or(self.is_not_empty(start[0], start[1],
                                         start[2], start[3]))
        update_condition.append(condition)

        condition = Or(self.is_not_empty(end[0], end[1], end[2], end[3]))
        update_condition.append(condition)

        if type(z) is int:
            # cover the case in which z > 0
            if z > 0:
                addend = [0, z, 0, 1]
                update_condition.append(self.add_vec(start, addend, y))

            # cover the case in which z < 0
            if z < 0:
                addend = [z, 0, 1, 0]
                update_condition.append(self.add_vec(start, addend, y))

            # cover the case in which z = 0
            if z == 0:
                assign = self.assign(y, start[0], start[1], start[2], start[3])
                update_condition.append(And(assign))

        # cover the case in which z is a variable
        else:
            if z in self.vars:
                z_val = self.vars[z]
            else:
                z_val = Int(z)
                self.vars[z] = z_val

            or_conditions = list()

            and_conditions = list()
            and_conditions.append(z_val > 0)
            and_conditions.append(self.add_vec(start, [0, z_val, 0, 1], y))
            or_conditions.append(And(and_conditions))

            and_conditions.clear()
            and_conditions.append(z_val < 0)
            and_conditions.append(self.add_vec(start, [z_val, 0, 1, 0], y))
            or_conditions.append(And(and_conditions))

            and_conditions.clear()
            and_conditions.append(z_val == 0)
            and_conditions.append(And(self.assign(y, start[0], start[1],
                                                  start[2], start[3])))
            or_conditions.append(And(and_conditions))

            update_condition.append(Or(or_conditions))

        # the sum is now stored in y, intersect this interval with both node
        # and automaton bounds
        update_condition += self.is_in_bounds(y, end, node_cond, y2)

        return And(update_condition)

    def is_in_bounds(self, start, end, node_cond, y2):
        condition = list()

        # intersect this with the automaton bound
        if self.automaton.get_lower_bound() == -float('inf'):
            incl_low = 2
            low = 0
        else:
            low = self.automaton.get_lower_bound()
            incl_low = 0

        if self.automaton.get_upper_bound() == float('inf'):
            incl_high = 2
            high = 0
        else:
            incl_high = 0
            high = self.automaton.get_upper_bound()

        interval = [low, high, incl_low, incl_high]

        condition.append(self.intersect_vec(start, interval, y2))

        # the result is now stored in y2
        # intersect this with the node bound
        cond_type = node_cond[0]
        cond_value = node_cond[1]

        if type(cond_value) is not int and not cond_value.isnumeric():
            if cond_value in self.vars:
                cond_value = self.vars[cond_value]
            else:
                cond_name = cond_value
                cond_value = Int(cond_value)
                self.vars[cond_name] = cond_value

        interval = []

        if cond_type == 0:
            interval = [cond_value, 0, 1, 2]
        elif cond_type == 1:
            interval = [0, cond_value, 2, 1]
        elif cond_type == 2:
            interval = [cond_value, cond_value, 1, 1]

        if interval:
            condition.append(self.intersect_vec(y2, interval, end))
        else:
            condition.append(And(self.assign(end, y2[0], y2[1], y2[2], y2[3])))

        return condition

    def solve(self):
        if self.s.check() == sat:
            print("Solution found")
            m = self.s.model()

            def empty(w, x, y, z):
                return y == 0 and z == 0 and w == x

            print("Intervals")
            for i in range(len(self.nodes)):
                print("\tNode: {}".format(self.nodes[i]))
                print("\treachability: {}".format(m[self.reachable[i]]))
                base_index = i * self.nr_of_intervals * 4
                # base_y = 0
                base_edge = i * self.nr_of_intervals
                for j in range(self.nr_of_intervals):
                    int_index = base_index + j * 4
                    edge_index = base_edge + j
                    b = m[self.intervals[int_index]]
                    t = m[self.intervals[int_index + 1]]
                    i_b = m[self.intervals[int_index + 2]]
                    i_t = m[self.intervals[int_index + 3]]
                    edge = m[self.used_edges[edge_index]]
                    if not empty(b, t, i_b, i_t):
                        print("\t\t[{}, {}, {}, {}] using {}".
                              format(b, t, i_b, i_t, edge))
                    # else:
                    #     print("\t\t[{}, {}, {}, {}] using {}".
                    #           format(b, t, i_b, i_t, edge))

            print("Variables")
            for var in self.vars:
                print("\t{}: {}".format(var, m[self.vars[var]]))

                # if i != 0:
                #     y1 = m[self.y[base_y]]
                #     y2 = m[self.y[base_y + 1]]
                #     y3 = m[self.y[base_y + 2]]
                #     y4 = m[self.y[base_y + 3]]
                #     y5 = m[self.y[base_y + 4]]
                #     y6 = m[self.y[base_y + 5]]
                #     y7 = m[self.y[base_y + 6]]
                #     y8 = m[self.y[base_y + 7]]
                #
                #     print("\t\ty1: [{}, {}, {}, {}]".format(y1, y2, y3, y4))
                #     print("\t\ty2: [{}, {}, {}, {}]".format(y5, y6, y7, y8))

        else:
            print("No solution found")

    @staticmethod
    def generate_interval(node_index, sub_index):
        interval = list()
        interval.append(Int("i_{}_{}_b".format(node_index, sub_index)))
        interval.append(Int("i_{}_{}_t".format(node_index, sub_index)))
        interval.append(Int("i_{}_{}_i_l".format(node_index, sub_index)))
        interval.append(Int("i_{}_{}_i_u".format(node_index, sub_index)))
        return interval

    def add_vec(self, start, addend, target):
        arguments = list()

        # if start is empty -> target = addend
        and_args = list()
        and_args += self.is_empty(start[0], start[1], start[2], start[3])
        and_args += self.assign(target,
                                addend[0], addend[1], addend[2], addend[3])
        arguments.append(And(and_args))

        # if addend is empty -> target = start
        and_args.clear()
        and_args += self.is_empty(addend[0], addend[1], addend[2], addend[3])
        and_args += self.assign(target,
                                start[0], start[1], start[2], start[3])
        arguments.append(And(and_args))

        # add b and t
        and_args.clear()

        and_args.append(
            Or(self.is_not_empty(addend[0], addend[1], addend[2], addend[3]))
        )
        and_args.append(
            Or(self.is_not_empty(start[0], start[1], start[2], start[3]))
        )

        for i in range(2):
            start_var = start[i]
            addend_var = addend[i]
            target_var = target[i]
            and_args.append(target_var == start_var + addend_var)

        for i in range(2, 4):
            start_var = start[i]
            addend_var = addend[i]
            target_var = target[i]
            and_args.append(
                self.generate_msum(start_var, addend_var, target_var)
            )
        arguments.append(And(and_args))

        return Or(arguments)

    @staticmethod
    def generate_msum(x, y, z):
        arguments = list()

        # 2 if max(x, y) == 2
        and_arguments = list()
        and_arguments.append(z == 2)
        and_arguments.append(Or(x == 2, y == 2))
        arguments.append(And(and_arguments))

        # x if x <= y
        and_arguments.clear()
        and_arguments.append(z == x)
        and_arguments.append(x <= y)
        arguments.append(And(and_arguments))

        # y if y < x
        and_arguments.clear()
        and_arguments.append(z == y)
        and_arguments.append(y < x)
        arguments.append(And(and_arguments))

        return Or(arguments)

    @staticmethod
    def is_empty(v_b, v_t, v_incl_low, v_incl_high):
        arguments = list()

        arguments.append(v_incl_low == 0)
        arguments.append(v_incl_high == 0)
        arguments.append(v_b == v_t)

        return arguments

    @staticmethod
    def is_not_empty(v_b, v_t, v_incl_low, v_incl_high):
        arguments = list()

        arguments.append(v_incl_low != 0)
        arguments.append(v_incl_high != 0)
        arguments.append(v_b != v_t)

        return arguments

    @staticmethod
    def assign(target, t_b, t_t, t_incl_low, t_incl_high):
        arguments = list()

        arguments.append(target[0] == t_b)
        arguments.append(target[1] == t_t)
        arguments.append(target[2] == t_incl_low)
        arguments.append(target[3] == t_incl_high)

        return arguments

    @staticmethod
    def overlaps(vector1, vector2):
        x_b = vector1[0]
        x_t = vector1[1]
        x_incl_low = vector1[2]
        x_incl_high = vector1[3]

        y_b = vector2[0]
        y_t = vector2[1]
        y_incl_low = vector2[2]
        y_incl_high = vector2[3]

        arguments = list()

        # y full infinity
        and_arguments = list()
        and_arguments.append(y_incl_low == 2)
        and_arguments.append(y_incl_high == 2)

        arguments.append(And(and_arguments))

        # x full infinity
        and_arguments = list()
        and_arguments.append(x_incl_low == 2)
        and_arguments.append(x_incl_high == 2)

        arguments.append(And(and_arguments))

        # y_b inside x
        and_arguments.clear()
        and_arguments.append(x_b < y_b)
        and_arguments.append(y_b < x_t)
        and_arguments.append(y_incl_low != 2)

        arguments.append(And(and_arguments))

        # y_t inside x
        and_arguments.clear()
        and_arguments.append(x_b < y_t)
        and_arguments.append(y_t < x_t)
        and_arguments.append(y_incl_high != 2)

        arguments.append(And(and_arguments))

        # x_b inside y
        and_arguments.clear()
        and_arguments.append(y_b < x_b)
        and_arguments.append(x_b < y_t)
        and_arguments.append(x_incl_low != 2)

        arguments.append(And(and_arguments))

        # x_t inside y
        and_arguments.clear()
        and_arguments.append(y_b < x_t)
        and_arguments.append(x_t < y_t)
        and_arguments.append(x_incl_high != 2)

        arguments.append(And(and_arguments))

        # x stretches over y at infinity on the right side
        and_arguments.clear()
        and_arguments.append(x_b <= y_b)
        and_arguments.append(x_incl_high == 2)

        arguments.append(And(and_arguments))

        # y stretches over x at infinity on the right side
        and_arguments.clear()
        and_arguments.append(y_b <= x_b)
        and_arguments.append(y_incl_high == 2)

        arguments.append(And(and_arguments))

        # x stretches over y at infinity on the left side
        and_arguments.clear()
        and_arguments.append(x_t >= y_t)
        and_arguments.append(x_incl_low == 2)

        arguments.append(And(and_arguments))

        # y stretches over x at infinity on the left side
        and_arguments.clear()
        and_arguments.append(y_t >= x_t)
        and_arguments.append(y_incl_low == 2)

        arguments.append(And(and_arguments))

        # xb == yb
        and_arguments.clear()
        and_arguments.append(x_b == y_b)
        and_arguments.append(x_incl_low == 1)
        and_arguments.append(y_incl_low == 1)

        arguments.append(And(and_arguments))

        # xb == yt
        and_arguments.clear()
        and_arguments.append(x_b == y_t)
        and_arguments.append(x_incl_low == 1)
        and_arguments.append(y_incl_high == 1)

        arguments.append(And(and_arguments))

        # xt == yb
        and_arguments.clear()
        and_arguments.append(x_t == y_b)
        and_arguments.append(x_incl_high == 1)
        and_arguments.append(y_incl_low == 1)

        arguments.append(And(and_arguments))

        # xt == yt
        and_arguments.clear()
        and_arguments.append(x_t == y_t)
        and_arguments.append(x_incl_high == 1)
        and_arguments.append(y_incl_high == 1)

        arguments.append(And(and_arguments))

        return Or(arguments)

    def no_overlaps(self, vector1, vector2):
        x_b = vector1[0]
        x_t = vector1[1]
        x_incl_low = vector1[2]
        x_incl_high = vector1[3]

        y_b = vector2[0]
        y_t = vector2[1]
        y_incl_low = vector2[2]
        y_incl_high = vector2[3]

        or_arguments = list()

        # x fully left of y
        and_arguments = list()
        and_arguments.append(x_t < y_b)
        and_arguments.append(x_incl_high != 2)
        and_arguments.append(y_incl_low != 2)
        or_arguments.append(And(and_arguments))

        # x fully right of y
        and_arguments.clear()
        and_arguments.append(y_t < x_b)
        and_arguments.append(y_incl_high != 2)
        and_arguments.append(x_incl_low != 2)
        or_arguments.append(And(and_arguments))

        # x shares lower edge with upper y but not inclusive
        and_arguments.clear()
        and_arguments.append(x_b == y_t)

        or_arguments2 = list()

        and_arguments2 = list()
        and_arguments2.append(x_incl_low == 0)
        and_arguments2.append(y_incl_high != 2)
        or_arguments2.append(And(and_arguments2))

        and_arguments2.clear()
        and_arguments2.append(x_incl_low != 2)
        and_arguments2.append(y_incl_high == 0)
        or_arguments2.append(And(and_arguments2))

        and_arguments.append(Or(or_arguments2))

        or_arguments.append(And(and_arguments))

        # y shares upper edge with lower y but not inclusive
        and_arguments.clear()
        and_arguments.append(x_t == y_b)

        or_arguments2.clear()

        and_arguments2.clear()
        and_arguments2.append(x_incl_high == 0)
        and_arguments2.append(y_incl_low != 2)
        or_arguments2.append(And(and_arguments2))

        and_arguments2.clear()
        and_arguments2.append(x_incl_high != 2)
        and_arguments2.append(y_incl_low == 0)
        or_arguments2.append(And(and_arguments2))

        and_arguments.append(Or(or_arguments2))

        or_arguments.append(And(and_arguments))

        # x is empty
        or_arguments.append(
            And(self.is_empty(x_b, x_t, x_incl_low, x_incl_high))
        )

        # y is empty
        or_arguments.append(
            And(self.is_empty(y_b, y_t, y_incl_low, y_incl_high))
        )

        return Or(or_arguments)

    def intersect_vec(self, vector1, vector2, target):
        arguments = list()

        x_b = vector1[0]
        x_t = vector1[1]
        x_incl_low = vector1[2]
        x_incl_high = vector1[3]

        y_b = vector2[0]
        y_t = vector2[1]
        y_incl_low = vector2[2]
        y_incl_high = vector2[3]

        z_b = target[0]
        z_t = target[1]
        z_incl_low = target[2]
        z_incl_high = target[3]

        # START: x and y do not overlap

        and_arguments = list()
        and_arguments.append(self.no_overlaps(vector1, vector2))
        and_arguments += self.assign(target, 0, 0, 0, 0)

        arguments.append(And(and_arguments))

        # STOP: x and y do not overlap
        # START: x and y overlap

        and_arguments.clear()
        and_arguments.append(self.overlaps(vector1, vector2))
        and_arguments.append(self.intersect_vec_one_bound(x_b, x_incl_low,
                                                          y_b, y_incl_low,
                                                          z_b, z_incl_low,
                                                          operator.lt))
        and_arguments.append(self.intersect_vec_one_bound(x_t, x_incl_high,
                                                          y_t, y_incl_high,
                                                          z_t, z_incl_high,
                                                          operator.gt))

        arguments.append(And(and_arguments))

        # STOP: x and y overlap

        return Or(arguments)

    @staticmethod
    def intersect_vec_one_bound(x_val, x_bound,
                                y_val, y_bound,
                                z_val, z_bound,
                                operation):
        or_arguments = list()

        # START: xv op yv

        and_arguments2 = list()
        and_arguments2.append(operation(x_val, y_val))

        or_arguments2 = list()

        #  ===== START: yb == 2

        and_arguments3 = list()
        and_arguments3.append(y_bound == 2)
        and_arguments3.append(z_bound == x_bound)
        and_arguments3.append(z_val == x_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: yb == 2
        # ===== START: yb != 2

        and_arguments3.clear()
        and_arguments3.append(y_bound != 2)
        and_arguments3.append(z_bound == y_bound)
        and_arguments3.append(z_val == y_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: yb != 2

        and_arguments2.append(Or(or_arguments2))
        or_arguments.append(And(and_arguments2))

        # STOP: xv op yv
        # START: yv op xv

        and_arguments2.clear()
        and_arguments2.append(operation(y_val, x_val))

        or_arguments2.clear()

        # ===== START xb == 2

        and_arguments3.clear()
        and_arguments3.append(x_bound == 2)
        and_arguments3.append(z_bound == y_bound)
        and_arguments3.append(z_val == y_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: xb == 2
        # ===== START: xb != 2

        and_arguments3.clear()
        and_arguments3.append(x_bound != 2)
        and_arguments3.append(z_bound == x_bound)
        and_arguments3.append(z_val == x_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: xb != 2

        and_arguments2.append(Or(or_arguments2))
        or_arguments.append(And(and_arguments2))

        # STOP: yv op xv
        # START: xv == yv

        and_arguments2.clear()
        and_arguments2.append(x_val == y_val)

        or_arguments2.clear()

        # ===== START: xb == 2

        and_arguments3.clear()
        and_arguments3.append(x_bound == 2)
        and_arguments3.append(z_bound == y_bound)
        and_arguments3.append(z_val == y_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: xb == 2
        # ===== START: yb == 2

        and_arguments3.clear()
        and_arguments3.append(y_bound == 2)
        and_arguments3.append(z_bound == x_bound)
        and_arguments3.append(z_val == x_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: yb == 2
        # ===== START: xb == 0

        and_arguments3.clear()
        and_arguments3.append(x_bound == 0)
        and_arguments3.append(z_bound == 0)
        and_arguments3.append(z_val == x_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: xb == 0
        # ===== START: yb == 0

        and_arguments3.clear()
        and_arguments3.append(y_bound == 0)
        and_arguments3.append(z_bound == 0)
        and_arguments3.append(z_val == y_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: yb == 0
        # ===== START: xb == 1, yb == 1

        and_arguments3.clear()
        and_arguments3.append(y_bound == 1)
        and_arguments3.append(x_bound == 1)
        and_arguments3.append(z_bound == 1)
        and_arguments3.append(z_val == y_val)

        or_arguments2.append(And(and_arguments3))

        # ===== STOP: xb == 1, yb == 1

        and_arguments2.append(Or(or_arguments2))
        or_arguments.append(And(and_arguments2))

        # STOP: xv == yv

        return Or(or_arguments)

    def union_vec(self, vector1, vector2, target):
        x_b = vector1[0]
        x_t = vector1[1]
        x_incl_b = vector1[2]
        x_incl_t = vector1[3]

        y_b = vector2[0]
        y_t = vector2[1]
        y_incl_b = vector2[2]
        y_incl_t = vector2[3]

        z_b = target[0]
        z_t = target[1]
        z_incl_b = target[2]
        z_incl_t = target[3]

        or_arguments = list()

        # START: x is empty

        empty_arguments = list()
        empty_arguments += self.is_empty(x_b, x_t, x_incl_b, x_incl_t)
        empty_arguments += self.assign(target, y_b, y_t, y_incl_b, y_incl_t)

        or_arguments.append(And(empty_arguments))

        # STOP: x is empty
        # START: y is empty

        empty_arguments.clear()
        empty_arguments += self.is_empty(y_b, y_t, y_incl_b, y_incl_t)
        empty_arguments += self.assign(target, x_b, x_t, x_incl_b, x_incl_t)

        or_arguments.append(And(empty_arguments))

        # STOP: y is empty
        # START: x and y is not empty

        not_empty_arguments = list()
        not_empty_arguments.append(
            Or(self.is_not_empty(x_b, x_t, x_incl_b, x_incl_t))
        )
        not_empty_arguments.append(
            Or(self.is_not_empty(y_b, y_t, y_incl_b, y_incl_t))
        )

        expr = self.union_vec_one_bound(x_b, x_incl_b,
                                        y_b, y_incl_b,
                                        z_b, z_incl_b,
                                        operator.lt)
        not_empty_arguments.append(expr)

        expr = self.union_vec_one_bound(x_t, x_incl_t,
                                        y_t, y_incl_t,
                                        z_t, z_incl_t,
                                        operator.gt)
        not_empty_arguments.append(expr)

        or_arguments.append(And(not_empty_arguments))

        # STOP: x and y is not empty

        return Or(or_arguments)

    @staticmethod
    def union_vec_one_bound(x_val, x_bound,
                            y_val, y_bound,
                            z_val, z_bound,
                            operation):

        or_arguments = list()

        # START: xb == 2

        and_arguments = list()
        and_arguments.append(x_bound == 2)
        and_arguments.append(z_bound == 2)
        and_arguments.append(z_val == 0)

        or_arguments.append(And(and_arguments))

        # STOP: xb == 2
        # START: yb == 2

        and_arguments.clear()
        and_arguments.append(y_bound == 2)
        and_arguments.append(z_bound == 2)
        and_arguments.append(z_val == 0)

        or_arguments.append(And(and_arguments))

        # STOP: yb == 2
        # START: yb != 2, xb != 2

        outer_and = list()
        outer_and.append(x_bound != 2)
        outer_and.append(y_bound != 2)

        outer_or = list()

        # ===== START: xv op yv

        and_arguments.clear()
        and_arguments.append(operation(x_val, y_val))
        and_arguments.append(z_bound == x_bound)
        and_arguments.append(z_val == x_val)

        outer_or.append(And(and_arguments))

        # ===== STOP: xv op yv
        # ===== START: yv op xv

        and_arguments.clear()
        and_arguments.append(operation(y_val, x_val))
        and_arguments.append(z_bound == y_bound)
        and_arguments.append(z_val == y_val)

        outer_or.append(And(and_arguments))

        # ===== STOP: yv op xv
        # ===== START: yv == xv

        and_arguments.clear()
        and_arguments.append(y_val == x_val)

        or_arguments2 = list()

        # ========== START: yb == 1 or xb = 1

        and_arguments2 = list()

        or_arguments3 = list()
        or_arguments3.append(y_bound == 1)
        or_arguments3.append(x_bound == 1)

        and_arguments2.append(Or(or_arguments3))

        and_arguments2.append(z_bound == 1)
        and_arguments2.append(z_val == x_val)

        or_arguments2.append(And(and_arguments2))

        # ========== STOP: yb == 1 or xb == 1
        # ========== START: yb == 0 and xb == 0

        and_arguments2.clear()

        and_arguments2.append(y_bound == 0)
        and_arguments2.append(x_bound == 0)
        and_arguments2.append(z_bound == 0)
        and_arguments2.append(z_val == x_val)

        or_arguments2.append(And(and_arguments2))

        # ========== STOP: yb == 0 and xb == 0

        and_arguments.append(Or(or_arguments2))
        outer_or.append(And(and_arguments))

        # ===== STOP: xv == yv

        outer_and.append(Or(outer_or))
        or_arguments.append(And(outer_and))

        # STOP: yb != 2, xb != 2

        return Or(or_arguments)

    def get_index_of_node(self, node):
        for i in range(len(self.nodes)):
            if self.nodes[i] == node:
                return i
        return None
