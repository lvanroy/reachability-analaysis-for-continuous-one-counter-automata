import unittest

from z3 import *

from Automaton.Automaton import Automaton

from Equations.EquationSolver import EquationSolver


class TestIntersection(unittest.TestCase):
    def setUp(self):
        automaton = Automaton("automaton", float('inf'), float('inf'))

        self.eq_solver = EquationSolver(automaton)

        self.solver = self.eq_solver.s

        self.vector1 = IntVector("a", 4)
        self.vector2 = IntVector("b", 4)
        self.result = IntVector("c", 4)

    def assign_to_vec(self, vector, b, t, ib, it):
        self.solver.add(vector[0] == b)
        self.solver.add(vector[1] == t)
        self.solver.add(vector[2] == ib)
        self.solver.add(vector[3] == it)

    def verify_result(self, t, b, ib, it):
        self.solver.check()
        m = self.solver.model()
        zt = m[self.result[0]].as_long()
        zb = m[self.result[1]].as_long()
        zl = m[self.result[2]].as_long()
        zu = m[self.result[3]].as_long()
        self.assertEqual(zb, b)
        self.assertEqual(zt, t)
        self.assertEqual(zl, ib)
        self.assertEqual(zu, it)

    def test_intersect_shared_x_upper_bound(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, 3, 6, 1, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(3, 3, 1, 1)

    def test_intersect_shared_x_lower_bound(self):
        self.assign_to_vec(self.vector1, 3, 6, 1, 1)
        self.assign_to_vec(self.vector2, 0, 3, 1, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(3, 3, 1, 1)

    def test_intersect_x_in_y(self):
        self.assign_to_vec(self.vector1, 0, 6, 0, 1)
        self.assign_to_vec(self.vector2, -5, 20, 2, 2)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 6, 0, 1)

    def test_intersect_y_in_x(self):
        self.assign_to_vec(self.vector1, 0, 6, 1, 1)
        self.assign_to_vec(self.vector2, 3, 3, 1, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(3, 3, 1, 1)

    def test_intersect_lower_infinity(self):
        self.assign_to_vec(self.vector1, 0, 6, 1, 1)
        self.assign_to_vec(self.vector2, 3, 3, 2, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 3, 1, 1)

    def test_intersect_double_infinity(self):
        self.assign_to_vec(self.vector1, -2, 6, 0, 0)
        self.assign_to_vec(self.vector2, 0, 0, 2, 2)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(-2, 6, 0, 0)

    def test_intersect_lower_match_not_included(self):
        self.assign_to_vec(self.vector1, 0, 1, 0, 1)
        self.assign_to_vec(self.vector2, 0, 1, 1, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 1, 0, 1)

    def test_no_intersect(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, 4, 6, 1, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)

    def test_no_intersect_on_bound(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 1)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)

    def test_no_intersect_inf_high(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 2)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)

    def test_no_intersect_inf_low(self):
        self.assign_to_vec(self.vector1, 0, 3, 2, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 0)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)

    def test_no_intersect_x_empty(self):
        self.assign_to_vec(self.vector1, 0, 0, 0, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 0)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)

    def test_no_intersect_y_empty(self):
        self.assign_to_vec(self.vector1, -3, 6, 0, 0)
        self.assign_to_vec(self.vector2, 0, 0, 0, 0)

        self.eq_solver.intersect_vec(self.vector1,
                                     self.vector2,
                                     self.result)

        self.verify_result(0, 0, 0, 0)
