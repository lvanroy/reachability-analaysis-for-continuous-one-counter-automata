import unittest

from z3 import IntVector, sat, unsat

from Automaton.Automaton import Automaton

from Equations.EquationSolver import EquationSolver


class TestOverlaps(unittest.TestCase):
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

    def test_overlap_x_covers_y(self):
        self.assign_to_vec(self.vector1, 0, 9, 1, 1)
        self.assign_to_vec(self.vector2, 3, 6, 1, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_y_covers_x(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, -3, 6, 1, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_no_overlap_shared_bound(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_no_overlap_no_shared_bound(self):
        self.assign_to_vec(self.vector1, 0, 2, 1, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_overlap_shared_lower_bound(self):
        self.assign_to_vec(self.vector1, 0, 3, 1, 1)
        self.assign_to_vec(self.vector2, 3, 6, 1, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_shared_upper_bound(self):
        self.assign_to_vec(self.vector1, 3, 6, 1, 1)
        self.assign_to_vec(self.vector2, 0, 3, 1, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_infinity_bound_upper(self):
        self.assign_to_vec(self.vector1, 4, 6, 1, 1)
        self.assign_to_vec(self.vector2, 0, 3, 1, 2)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_infinity_bound_lower(self):
        self.assign_to_vec(self.vector1, 4, 6, 2, 1)
        self.assign_to_vec(self.vector2, 0, 3, 1, 0)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_double_infinity_high_zero(self):
        self.assign_to_vec(self.vector1, -2, 6, 0, 0)
        self.assign_to_vec(self.vector2, 0, 0, 2, 2)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_double_infinity_low_zero(self):
        self.assign_to_vec(self.vector1, -4, 2, 0, 0)
        self.assign_to_vec(self.vector2, -6, -4, 2, 2)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_lower_match_not_included(self):
        self.assign_to_vec(self.vector1, 0, 1, 0, 1)
        self.assign_to_vec(self.vector2, 0, 0, 1, 2)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), sat)

    def test_overlap_infinity_bound_lower_no_overlap(self):
        self.assign_to_vec(self.vector1, 4, 6, 0, 1)
        self.assign_to_vec(self.vector2, 0, 3, 2, 0)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_overlap_infinity_bound_upper_no_overlap(self):
        self.assign_to_vec(self.vector1, 4, 6, 1, 2)
        self.assign_to_vec(self.vector2, 0, 3, 1, 0)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_overlap_ignore_infinity_ignore_lower_bound(self):
        self.assign_to_vec(self.vector1, -1, 1, 0, 0)
        self.assign_to_vec(self.vector2, 0, -5, 2, 1)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)

    def test_overlap_ignore_infinity_ignore_upper_bound(self):
        self.assign_to_vec(self.vector1, -1, 1, 0, 0)
        self.assign_to_vec(self.vector2, 10, 0, 1, 2)

        self.solver.add(self.eq_solver.overlaps(self.vector1,
                                                self.vector2))

        self.assertEqual(self.solver.check(), unsat)
