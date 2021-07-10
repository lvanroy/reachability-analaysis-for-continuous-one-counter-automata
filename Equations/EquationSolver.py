from z3 import *
from typing import List, Dict

import operator


class EquationSolver:
    def __init__(self, automaton, goal_node=None):
        self.automaton = automaton
        self.s = Solver()
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

        # the transition objects created for our formula
        # each of these transitions will match one edge
        # every three consecutive entries form one transition
        #   s0, z0, e0, s1, z1, e1, ...
        self.transitions: List[ArithRef] = list()

        # the intervals used within the different stages.Each four
        # consecutive entries will match the interval for one
        # specific node where the first interval matches node 0
        #   b0, t0, ⊥0, ⊤0, b1, t1, ⊥1, ⊤1, ...
        self.intervals: List[ArithRef] = list()

        # keep track of the found parameters
        # this is so that we reuse the same variable every time
        # we refer to this parameter, rather than creating a new one
        self.parameters: Dict[str, IntVal] = dict()

        # track the final transition
        # this transition must end in the goal node
        # for it to be marked final
        self.m = Int('m')

        # mark the goal node if there is any
        self.goal_node = goal_node

        # track the reachability of nodes
        self.reachable = dict()

    def analyse(self):
        self.build_transitions()
        self.build_intervals()
        self.add_initial_condition()
        self.add_sequential_condition()

        if self.goal_node is not None:
            if self.automaton.is_initial(self.goal_node):
                print("Node {} is reachable as it is the initial node".format(self.goal_node))
            self.add_final_condition(self.goal_node)
            self.solve()
        else:
            for node in self.nodes:
                print("\nSolving for node {}".format(node))
                if self.automaton.is_initial(node):
                    print("Node {} is reachable as it is the initial node".format(node))
                else:
                    self.s.push()
                    self.add_final_condition(node)
                    self.reachable[node] = self.s.check() == sat
                    self.solve()
                    self.s.pop()

    def get_index_of_node(self, node):
        for i in range(len(self.nodes)):
            if self.nodes[i] == node:
                return i
        return None

    def build_transitions(self):
        # fetch all edges from the automaton
        # convert each edge to [from, op, end] format
        # from and end are mapped to integers where
        # each integer represents a node
        for start in self.nodes:
            for end in self.automaton.get_outgoing_edges(start):
                edge = self.automaton.get_edge(start, end)
                start_index = self.get_index_of_node(edge.get_start())
                end_index = self.get_index_of_node(edge.get_end())
                end_condition = self.automaton.get_node_condition(end)
                if edge.get_operation() is not None:
                    operation = edge.get_operation().get_value()
                else:
                    operation = 0

                transition = list()
                transition.append(start_index)
                transition.append(operation)
                transition.append(end_index)
                self.edges += transition

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

        # create a sequence of transitions
        # each transition is a sequence of integers
        # format: [p, z, q]
        for i in range(len(self.nodes) - 1):
            transition = IntVector('t{}'.format(i), 3)
            condition = IntVector('c{}'.format(i), 2)
            or_arguments = list()
            for j in range(0, len(self.edges), 3):
                and_arguments = list()
                for k in range(3):
                    val = self.edges[j + k]
                    if str(val).lstrip("-").isnumeric():
                        and_arguments.append(transition[k] == val)
                    else:
                        if val in self.parameters:
                            param = self.parameters[val]
                        else:
                            param = Int(val)
                            self.parameters[val] = param
                        and_arguments.append(transition[k] == param)
                for k in range(2):
                    index = int(j / 3 * 2) + k
                    and_arguments.append(condition[k] == self.conditions[index])
                or_arguments.append(And(and_arguments))
            expr = Or(or_arguments)
            self.s.add(expr)
            self.transitions += transition
            self.selected_conditions += condition

    def build_intervals(self):
        # initialise all intervals
        for r in range(len(self.nodes)+1):
            for n in range(len(self.nodes)):
                self.intervals += self.generate_interval(r, n)

        for i in range(len(self.nodes)):
            base = i * 4
            if i == 0:
                initial_value = self.automaton.get_initial_value()
                self.s.add(self.intervals[base] == initial_value)
                self.s.add(self.intervals[base + 1] == initial_value)
                self.s.add(self.intervals[base + 2] == 1)
                self.s.add(self.intervals[base + 3] == 1)
            else:
                self.s.add(self.intervals[base] == 0)
                self.s.add(self.intervals[base + 1] == 0)
                self.s.add(self.intervals[base + 2] == 0)
                self.s.add(self.intervals[base + 3] == 0)

        # define the evolution of the intervals
        for it in range(len(self.nodes) - 1):
            for interval in range(len(self.nodes)):
                if it + 1 == interval:
                    self.update_interval(it)
                else:
                    base = it * (len(self.nodes) + 1) * 4 + interval * 4
                    target = base + (len(self.nodes) + 1) * 4
                    start_interval = self.intervals[base: base + 4]
                    target_interval = self.intervals[target: target + 4]
                    expr = self.assign(target_interval,
                                       start_interval[0],
                                       start_interval[1],
                                       start_interval[2],
                                       start_interval[3])
                    self.s.add(And(expr))

    @staticmethod
    def generate_interval(r, node_index):
        interval = list()
        interval.append(Int("i_{}_{}_b".format(r, node_index)))
        interval.append(Int("i_{}_{}_t".format(r, node_index)))
        interval.append(Int("i_{}_{}_i_l".format(r, node_index)))
        interval.append(Int("i_{}_{}_i_u".format(r, node_index)))
        return interval

    def update_interval(self, it):
        z = self.transitions[it * 3 + 1]

        base = it * (len(self.nodes) + 1) * 4 + it * 4
        end = base + 4
        target = end + (len(self.nodes) + 1) * 4

        start_interval = self.intervals[base: base + 4]
        end_interval = self.intervals[end: end + 4]
        target_interval = self.intervals[target: target + 4]

        update_condition = list()

        vec_name = 'y{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        y = IntVector(vec_name, 4)

        or_arguments = list()

        # cover the case in which z > 0
        and_args = list()
        and_args.append(z > 0)

        addend_name = 'addend{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        addend = IntVector(addend_name, 4)

        and_args += self.assign(addend, 0, z, 0, 1)
        and_args.append(self.add_vec(start_interval,
                                     addend,
                                     y))

        or_arguments.append(And(and_args))

        # cover the case in which z < 0
        and_args.clear()
        and_args.append(z < 0)

        addend_name = 'addend{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        addend2 = IntVector(addend_name, 4)

        and_args += self.assign(addend2, z, 0, 1, 0)
        and_args.append(self.add_vec(start_interval,
                                     addend2,
                                     y))

        or_arguments.append(And(and_args))

        # cover the case in which z = 0
        and_args.clear()
        and_args.append(z == 0)

        and_args += self.assign(y,
                                start_interval[0],
                                start_interval[1],
                                start_interval[2],
                                start_interval[3])
        or_arguments.append(And(and_args))

        update_condition.append(Or(or_arguments))

        # the sum is now stored in y
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

        vec_name = 'ab{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        interval = IntVector(vec_name, 4)
        update_condition.append(
            And(
                self.assign(interval,
                            low, high,
                            incl_low, incl_high)
            )
        )

        vec_name = 'y{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        y2 = IntVector(vec_name, 4)

        self.intersect_vec(y, interval, y2)

        # the result is now stored in y2
        # intersect this with the node bound
        condition = self.selected_conditions[it * 2]
        value = self.selected_conditions[it * 2 + 1]

        vec_name = 'ab{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        interval = IntVector(vec_name, 4)

        or_arguments = list()
        or_arguments.append(
            And(
                condition == 0,
                And(self.assign(interval, value, 0, 1, 2))
            )
        )
        or_arguments.append(
            And(
                condition == 1,
                And(self.assign(interval, 0, value, 2, 1))
            )
        )
        or_arguments.append(
            And(
                condition == 2,
                And(self.assign(interval, value, value, 1, 1))
            )
        )
        or_arguments.append(
            And(
                condition == 3,
                And(self.assign(interval, 0, 0, 2, 2))
            )
        )

        update_condition.append(Or(or_arguments))

        vec_name = 'y{}'.format(self.auxiliary_counter)
        self.auxiliary_counter += 1
        y3 = IntVector(vec_name, 4)

        self.intersect_vec(y2, interval, y3)

        # the result is now stored in y3
        # take the union with this vector and the original interval
        self.union_vec(end_interval, y3, target_interval)

        # ensure that the result is not empty
        # if this is the case it means that the node is not reachable
        update_condition.append(Or(
            self.is_not_empty(
                target_interval[0],
                target_interval[1],
                target_interval[2],
                target_interval[3]
            )
        ))

        self.s.add(
            Or(
                And(update_condition),
                it > self.m
            )
        )

    def add_vec(self, start, addend, target):
        arguments = list()

        # if start is empty -> target = addend
        and_arguments = list()
        and_arguments += self.is_empty(
            start[0],
            start[1],
            start[2],
            start[3]
        )
        and_arguments += self.assign(
            target,
            addend[0],
            addend[1],
            addend[2],
            addend[3]
        )
        arguments.append(And(and_arguments))

        # if addend is empty -> target = start
        and_arguments.clear()
        and_arguments += self.is_empty(
            addend[0],
            addend[1],
            addend[2],
            addend[3]
        )
        and_arguments += self.assign(
            target,
            start[0],
            start[1],
            start[2],
            start[3]
        )
        arguments.append(And(and_arguments))

        # add b and t
        and_arguments.clear()
        and_arguments.append(
            Or(self.is_not_empty(
                addend[0],
                addend[1],
                addend[2],
                addend[3]
            )
            ))
        and_arguments.append(
            Or(self.is_not_empty(
                start[0],
                start[1],
                start[2],
                start[3]
            )
            ))
        for i in range(2):
            start_var = start[i]
            addend_var = addend[i]
            target_var = target[i]
            and_arguments.append(target_var == start_var + addend_var)

        for i in range(2, 4):
            start_var = start[i]
            addend_var = addend[i]
            target_var = target[i]
            and_arguments.append(
                self.generate_msum(start_var, addend_var, target_var)
            )
        arguments.append(And(and_arguments))

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

        self.s.add(Or(arguments))

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

        or_arguments = list()

        # START: x is empty

        empty_arguments = list()
        empty_arguments += self.is_empty(x_b, x_t, x_incl_low, x_incl_high)
        empty_arguments += self.assign(target, y_b, y_t, y_incl_low, y_incl_high)

        or_arguments.append(And(empty_arguments))

        # STOP: x is empty
        # START: y is empty

        empty_arguments.clear()
        empty_arguments += self.is_empty(y_b, y_t, y_incl_low, y_incl_high)
        empty_arguments += self.assign(target, x_b, x_t, x_incl_low, x_incl_high)

        or_arguments.append(And(empty_arguments))

        # STOP: y is empty
        # START: x and y is not empty

        not_empty_arguments = list()
        not_empty_arguments.append(
            Or(self.is_not_empty(x_b, x_t, x_incl_low, x_incl_high))
        )
        not_empty_arguments.append(
            Or(self.is_not_empty(y_b, y_t, y_incl_low, y_incl_high))
        )

        expr = self.union_vec_one_bound(x_b, x_incl_low,
                                        y_b, y_incl_low,
                                        z_b, z_incl_low,
                                        operator.lt)
        not_empty_arguments.append(expr)

        expr = self.union_vec_one_bound(x_t, x_incl_high,
                                        y_t, y_incl_high,
                                        z_t, z_incl_high,
                                        operator.gt)
        not_empty_arguments.append(expr)

        or_arguments.append(And(not_empty_arguments))

        # STOP: x and y is not empty

        self.s.add(Or(or_arguments))

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

    def add_initial_condition(self):
        # ensure that our first transition starts in
        # the initial node of the automaton
        start_node = self.automaton.get_initial_node()
        start_index = self.get_index_of_node(start_node)
        self.s.add(self.transitions[0] == start_index)

    def add_sequential_condition(self):
        # either two subsequent transitions much follow up
        # on each other or the goal node must already be reached
        and_arguments = list()
        for i in range(2, len(self.transitions) - 3, 3):
            end_node = self.transitions[i]
            start_node = self.transitions[i + 1]
            and_arguments.append(Or(end_node == start_node, (i - 2) / 3 >= self.m))
        self.s.add(And(and_arguments))

    def add_final_condition(self, goal):
        # ensure that there is a transition which goes
        # towards the goal node. Track the index of this
        # transition with the variable m
        or_arguments = list()
        goal_index = self.get_index_of_node(goal)
        for i in range(2, len(self.transitions), 3):
            end_node = self.transitions[i]
            arg = And(end_node == goal_index, self.m == (i - 2) / 3)
            or_arguments.append(arg)
        self.s.add(Or(or_arguments))

    def solve(self):
        if self.s.check() == sat:
            m = self.s.model()

            condition_to_string = {
                0: ">=",
                1: "<=",
                2: "==",
                3: "no condition"
            }

            print("m = {}".format(m[self.m]))

            print("\nparameters:")
            for val in self.parameters:
                print("{} = {}".format(val, m[self.parameters[val]]))

            print("\ntransitions:")
            for i in range(m[self.m].as_long() + 1):
                print("{}, {}, {}".format(
                    self.nodes[m[self.transitions[i * 3]].as_long()],
                    m[self.transitions[(i * 3) + 1]],
                    self.nodes[m[self.transitions[(i * 3) + 2]].as_long()]
                ))
                condition = condition_to_string[m[self.selected_conditions[i * 2]].as_long()]
                if condition == "no condition":
                    print("no end condition")
                else:
                    print("end cond: {} {}".format(
                        condition,
                        m[self.selected_conditions[(i * 2) + 1]].as_long()
                    ))

            print("\nintervals:")
            for r in range(m[self.m].as_long() + 2):
                interval_offset = (len(self.nodes) + 1) * 4 * r
                print("Round {}".format(r))
                for j in range(m[self.m].as_long() + 2):
                    start_index = interval_offset + j * 4
                    b = self.intervals[start_index]
                    t = self.intervals[start_index + 1]
                    i_l = self.intervals[start_index + 2]
                    i_h = self.intervals[start_index + 2]
                    print("s{}= [{}, {}, {}, {}]".format(
                        j,
                        m[b].as_long(),
                        m[t].as_long(),
                        m[i_l].as_long(),
                        m[i_h].as_long()
                    ))
        else:
            print("No solution found")
        print("===========")
