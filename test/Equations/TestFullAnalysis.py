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
                      min_bound=float('inf'),
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

    def test_single_path_automaton(self):
        self.create_solver("input/single_path.dot")

        self.analyze()

        self.solver.push()
        self.eq_solver.add_final_condition("s1")
        self.assertEqual(self.solver.check(), sat)
        self.assertEquals(self.solver.model()[self.eq_solver.m].as_long(), 0)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s2")
        self.assertEqual(self.solver.check(), sat)
        self.assertEquals(self.solver.model()[self.eq_solver.m].as_long(), 1)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition("s3")
        self.assertEqual(self.solver.check(), sat)
        self.assertEquals(self.solver.model()[self.eq_solver.m].as_long(), 2)
        self.solver.pop()
