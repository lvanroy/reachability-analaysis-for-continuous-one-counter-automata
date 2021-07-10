import unittest
import os

from z3 import *

from Automaton.DotReader import DotReader

from Equations.EquationSolver import EquationSolver


class TestFullAnalysis(unittest.TestCase):
    @staticmethod
    def build_file_path(file):
        base = os.path.dirname(__file__)
        return os.path.join(base, file)

    def create_solver(self, file_name,
                      min_bound=-float('inf'),
                      max_bound=float('inf'),
                      initial_val=0):
        file_name = self.build_file_path(file_name)
        reader = DotReader(file_name)
        automaton = reader.create_automaton()
        automaton.set_lower_bound(min_bound)
        automaton.set_upper_bound(max_bound)
        automaton.set_initial_value(initial_val)

        self.eq_solver = EquationSolver(automaton)

        self.solver = self.eq_solver.s

    def analyze(self):
        self.eq_solver.build_transitions()
        self.eq_solver.build_intervals()
        self.eq_solver.add_initial_condition()
        self.eq_solver.add_sequential_condition()

    def print(self):
        if self.solver.check() == sat:
            m = self.solver.model()

            condition_to_string = {
                0: ">=",
                1: "<=",
                2: "==",
                3: "no condition"
            }

            print("m = {}".format(m[self.eq_solver.m]))

            print("\nparameters:")
            for val in self.eq_solver.parameters:
                print("{} = {}".format(val, m[self.eq_solver.parameters[val]]))

            print("\ntransitions:")
            for i in range(len(self.eq_solver.nodes)-1):
                print("{}, {}, {}".format(
                    self.eq_solver.nodes[m[self.eq_solver.transitions[i * 3]].as_long()],
                    m[self.eq_solver.transitions[(i * 3) + 1]],
                    self.eq_solver.nodes[m[self.eq_solver.transitions[(i * 3) + 2]].as_long()]
                ))
                condition = condition_to_string[m[self.eq_solver.selected_conditions[i * 2]].as_long()]
                if condition == "no condition":
                    print("no end condition")
                else:
                    print("end cond: {} {}".format(
                        condition,
                        m[self.eq_solver.selected_conditions[(i * 2) + 1]].as_long()
                    ))

            print("\nintervals:")
            for r in range(len(self.eq_solver.nodes)):
                interval_offset = (len(self.eq_solver.nodes) + 1) * 4 * r
                print("Round {}".format(r))
                for j in range(len(self.eq_solver.nodes)):
                    start_index = interval_offset + j * 4
                    b = self.eq_solver.intervals[start_index]
                    t = self.eq_solver.intervals[start_index + 1]
                    i_l = self.eq_solver.intervals[start_index + 2]
                    i_h = self.eq_solver.intervals[start_index + 2]
                    if m[b] is None or m[t] is None:
                        print("s{} = None".format(j))
                        continue
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

    def verify_interval_matches(self, interval, index, b_ex, t_ex, il_ex, ih_ex):
        interval_offset = (len(self.eq_solver.nodes) + 1) * 4 * interval
        start_index = interval_offset + index * 4

        intervals = self.eq_solver.intervals
        model = self.solver.model()

        b_acc = intervals[start_index]
        t_acc = intervals[start_index + 1]
        il_acc = intervals[start_index + 2]
        ih_acc = intervals[start_index + 3]

        self.assertEqual(model[b_acc].as_long(), b_ex)
        self.assertEqual(model[t_acc].as_long(), t_ex)
        self.assertEqual(model[il_acc].as_long(), il_ex)
        self.assertEqual(model[ih_acc].as_long(), ih_ex)

    def test_single_path_automaton(self):
        self.create_solver("input/single_path.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 0)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 1)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(0, 2, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.verify_interval_matches(1, 2, 0, 0, 0, 0)
        self.verify_interval_matches(2, 0, 0, 0, 1, 1)
        self.verify_interval_matches(2, 1, 0, 0, 1, 1)
        self.verify_interval_matches(2, 2, 0, 1, 0, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 2)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(0, 2, 0, 0, 0, 0)
        self.verify_interval_matches(0, 3, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.verify_interval_matches(1, 2, 0, 0, 0, 0)
        self.verify_interval_matches(1, 3, 0, 0, 0, 0)
        self.verify_interval_matches(2, 0, 0, 0, 1, 1)
        self.verify_interval_matches(2, 1, 0, 0, 1, 1)
        self.verify_interval_matches(2, 2, 0, 1, 0, 1)
        self.verify_interval_matches(2, 3, 0, 0, 0, 0)
        self.verify_interval_matches(3, 0, 0, 0, 1, 1)
        self.verify_interval_matches(3, 1, 0, 0, 1, 1)
        self.verify_interval_matches(3, 2, 0, 1, 0, 1)
        self.verify_interval_matches(3, 3, -1, 1, 0, 0)
        self.solver.pop()

    def test_single_path_with_condition(self):
        self.create_solver("input/single_path_with_conditions.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 0)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 1)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(0, 2, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.verify_interval_matches(1, 2, 0, 0, 0, 0)
        self.verify_interval_matches(2, 0, 0, 0, 1, 1)
        self.verify_interval_matches(2, 1, 0, 0, 1, 1)
        self.verify_interval_matches(2, 2, 0, 1, 0, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 2)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(0, 2, 0, 0, 0, 0)
        self.verify_interval_matches(0, 3, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.verify_interval_matches(1, 2, 0, 0, 0, 0)
        self.verify_interval_matches(1, 3, 0, 0, 0, 0)
        self.verify_interval_matches(2, 0, 0, 0, 1, 1)
        self.verify_interval_matches(2, 1, 0, 0, 1, 1)
        self.verify_interval_matches(2, 2, 0, 1, 0, 1)
        self.verify_interval_matches(2, 3, 0, 0, 0, 0)
        self.verify_interval_matches(3, 0, 0, 0, 1, 1)
        self.verify_interval_matches(3, 1, 0, 0, 1, 1)
        self.verify_interval_matches(3, 2, 0, 1, 0, 1)
        self.verify_interval_matches(3, 3, -1, 0, 0, 1)
        self.solver.pop()

    def test_single_path_not_satisfiable(self):
        self.create_solver("input/single_path_not_satisfiable.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 0)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 1)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(0, 2, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 0, 0, 1, 1)
        self.verify_interval_matches(1, 2, 0, 0, 0, 0)
        self.verify_interval_matches(2, 0, 0, 0, 1, 1)
        self.verify_interval_matches(2, 1, 0, 0, 1, 1)
        self.verify_interval_matches(2, 2, 0, 1, 0, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()

    def test_path_with_parameter(self):
        self.create_solver("input/simple_func_reachability_automaton_foo.dot")

        self.analyze()

        self.eq_solver.add_final_condition("Q8")
        self.assertEqual(self.solver.check(), sat)
        m = self.solver.model()[self.eq_solver.m].as_long()
        self.verify_interval_matches(m, m, 5, 5, 1, 1)

    def test_multi_path(self):
        self.create_solver("input/multi_path.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), sat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s4")
        self.assertEqual(self.solver.check(), sat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s5")
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()
