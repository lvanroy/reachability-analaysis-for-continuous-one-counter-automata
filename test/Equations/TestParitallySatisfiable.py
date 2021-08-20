import unittest
import os

from z3 import sat, unsat

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

    def analyze(self, nr_of_intervals):
        self.nr_of_intervals = nr_of_intervals

        self.eq_solver.nr_of_intervals = nr_of_intervals

        self.eq_solver.build_transitions()
        self.eq_solver.build_node_conditions()
        self.eq_solver.build_intervals()
        self.eq_solver.analyse_loops()
        self.eq_solver.add_successor_condition()
        self.eq_solver.add_reachability_condition()

    def verify_not_empty(self, node):
        m = self.solver.model()

        base_index = node * self.nr_of_intervals * 4
        base_edge = node * self.nr_of_intervals

        def empty(w, x, y, z):
            return y == 0 and z == 0 and w == x

        success = False

        for i in range(self.nr_of_intervals):
            int_index = base_index + i * 4
            edge_index = base_edge + i
            interval = self.eq_solver.intervals[int_index: int_index+4]
            b = m[interval[0]]
            t = m[interval[1]]
            i_b = m[interval[2]]
            i_t = m[interval[3]]
            edge = m[self.eq_solver.used_edges[edge_index]].as_long()

            if not empty(b, t, i_b, i_t):
                if edge != -2:
                    success = True
                    break

        self.assertTrue(success)

    def testParitallySatisfiable(self):
        self.create_solver("input/partially_satisfiable.dot")

        self.analyze(1)

        nodes = self.eq_solver.nodes

        self.solver.push()
        self.eq_solver.add_final_condition(nodes.index("s1"))
        self.assertEqual(self.solver.check(), sat)
        self.verify_not_empty(nodes.index("s1"))
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition(nodes.index("s2"))
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()

        self.solver.push()
        self.eq_solver.add_final_condition(nodes.index("s3"))
        self.assertEqual(self.solver.check(), unsat)
        self.solver.pop()
