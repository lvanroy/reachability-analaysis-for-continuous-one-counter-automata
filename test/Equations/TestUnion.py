import unittest

from z3 import IntVector, sat, And

from Automaton.Automaton import Automaton

from Equations.EquationSolver import EquationSolver


class TestUnion(unittest.TestCase):
    def setUp(self):
        automaton = Automaton("automaton", float('inf'), float('inf'))

        self.eq_solver = EquationSolver(automaton)

        self.s = self.eq_solver.s

        self.vector1 = IntVector("a", 4)
        self.vector2 = IntVector("b", 4)
        self.result = IntVector("c", 4)

    def assign_to_vec(self, vector, b, t, ib, it):
        self.s.add(
            And(
                vector[0] == b,
                vector[1] == t,
                vector[2] == ib,
                vector[3] == it
            )
        )

    def verify_result(self, t, b, ib, it):
        self.assertEqual(self.s.check(), sat)
        m = self.s.model()
        zt = m[self.result[0]].as_long()
        zb = m[self.result[1]].as_long()
        zl = m[self.result[2]].as_long()
        zu = m[self.result[3]].as_long()
        self.assertEqual(zb, b)
        self.assertEqual(zt, t)
        self.assertEqual(zl, ib)
        self.assertEqual(zu, it)

    def test_union_x_in_y(self):
        self.assign_to_vec(self.vector1, 0, 3, 0, 0)
        self.assign_to_vec(self.vector2, -3, 6, 0, 0)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(-3, 6, 0, 0)

    def test_union_y_in_x(self):
        self.assign_to_vec(self.vector1, 0, 10, 0, 1)
        self.assign_to_vec(self.vector2, 3, 6, 1, 0)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(0, 10, 0, 1)

    def test_union_infinity_bound_lower(self):
        self.assign_to_vec(self.vector1, 0, 10, 0, 1)
        self.assign_to_vec(self.vector2, 3, 6, 2, 0)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(0, 10, 2, 1)

    def test_union_infinity_bound_upper(self):
        self.assign_to_vec(self.vector1, 0, 10, 0, 2)
        self.assign_to_vec(self.vector2, 3, 6, 0, 0)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(0, 0, 0, 2)

    def test_union_x_empty(self):
        self.assign_to_vec(self.vector1, 0, 0, 0, 0)
        self.assign_to_vec(self.vector2, 3, 6, 0, 2)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(3, 6, 0, 2)

    def test_union_y_empty(self):
        self.assign_to_vec(self.vector1, 3, 6, 0, 2)
        self.assign_to_vec(self.vector2, 0, 0, 0, 0)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(3, 6, 0, 2)

    def test_union_x_shared_upper_bound(self):
        self.assign_to_vec(self.vector1, 3, 6, 0, 1)
        self.assign_to_vec(self.vector2, 6, 9, 0, 1)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(3, 9, 0, 1)

    def test_union_x_shared_lower_bound(self):
        self.assign_to_vec(self.vector1, 3, 6, 1, 1)
        self.assign_to_vec(self.vector2, 0, 3, 0, 1)

        self.s.add(self.eq_solver.union_vec(self.vector1,
                                            self.vector2,
                                            self.result))

        self.verify_result(0, 6, 0, 1)
