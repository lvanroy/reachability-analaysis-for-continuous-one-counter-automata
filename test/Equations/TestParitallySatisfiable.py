import unittest

from z3 import *

from Automaton.DotReader import DotReader

from Equations.EquationSolver import EquationSolver


class TestPartiallySatisfiable(unittest.TestCase):
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

    def testParitallySatisfiable(self):
        self.create_solver("input/partially_satisfiable.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.assertEqual(self.solver.model()[self.eq_solver.m].as_long(), 0)
        self.verify_interval_matches(0, 0, 0, 0, 1, 1)
        self.verify_interval_matches(0, 1, 0, 0, 0, 0)
        self.verify_interval_matches(1, 0, 0, 0, 1, 1)
        self.verify_interval_matches(1, 1, 1, 1, 1, 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()
