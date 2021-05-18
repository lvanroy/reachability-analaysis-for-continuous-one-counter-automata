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