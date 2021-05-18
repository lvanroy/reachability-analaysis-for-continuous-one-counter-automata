import unittest

from z3 import *

from Automaton.Automaton import Automaton

from Equations.EquationSolver import EquationSolver


class TestNoOverlaps(unittest.TestCase):
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

    def test_no_overlap_x_fully_left_of_y(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, 4, 6, 1, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_fully_right_of_y(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, -4, -6, 0, 0)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_low_matches_y_high1(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, 3, 6, 0, 0)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_low_matches_y_high2(self):
        self.assign_to_vec(self.vector1, 0, 3, 0, 0)
        self.assign_to_vec(self.vector2, 3, 6, 1, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_high_matches_y_low1(self):
        self.assign_to_vec(self.vector1, -5, -2, 1, 1)
        self.assign_to_vec(self.vector2, -2, 5, 0, 0)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_high_matches_y_low2(self):
        self.assign_to_vec(self.vector1, -5, -2, 0, 0)
        self.assign_to_vec(self.vector2, -2, 6, 1, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_empty(self):
        self.assign_to_vec(self.vector1, 0, 0, 0, 0)
        self.assign_to_vec(self.vector2, -2, 6, 1, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_x_inside_y(self):
        self.assign_to_vec(self.vector1, 0, 4, 0, 0)
        self.assign_to_vec(self.vector2, 2, 6, 1, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_y_inside_x(self):
        self.assign_to_vec(self.vector1, 2, 6, 1, 2)
        self.assign_to_vec(self.vector2, 0, 4, 1, 0)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_infinity_bound_lower(self):
        self.assign_to_vec(self.vector1, -6, -2, 1, 2)
        self.assign_to_vec(self.vector2, 0, 4, 2, 0)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_infinity_bound_upper(self):
        self.assign_to_vec(self.vector1, 10, 25, 1, 2)
        self.assign_to_vec(self.vector2, 0, 4, 0, 2)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_double_infinity_low_zero(self):
        self.assign_to_vec(self.vector1, -2, 6, 0, 0)
        self.assign_to_vec(self.vector2, 0, 0, 2, 2)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_double_infinity_high_zero(self):
        self.assign_to_vec(self.vector1, -3, 6, 1, 0)
        self.assign_to_vec(self.vector2, 6, 6, 2, 2)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_lower_match_not_included(self):
        self.assign_to_vec(self.vector1, 0, 1, 0, 1)
        self.assign_to_vec(self.vector2, 0, 0, 1, 2)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_ignore_infinity_bound_lower(self):
        self.assign_to_vec(self.vector1, -1, 1, 0, 0)
        self.assign_to_vec(self.vector2, 0, -5, 2, 1)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_ignore_infinity_bound_upper(self):
        self.assign_to_vec(self.vector1, -1, 1, 0, 0)
        self.assign_to_vec(self.vector2, 10, 0, 1, 2)

        self.solver.add(self.eq_solver.no_overlaps(self.vector1,
                                                   self.vector2))

        self.assertEqual(self.solver.check(), sat)




