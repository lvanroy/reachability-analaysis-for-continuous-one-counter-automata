import unittest

from test.Automaton.TestCreateAutomaton import TestCreateAutomaton
from test.Automaton.TestLoopFinder import TestLoopFinder

from test.Reach.TestIntervals import TestIntervals
from test.Reach.TestNewReachConfiguration import TestNewReachConfiguration
from test.Reach.TestPostUpdate import TestPostUpdate
from test.Reach.TestLoopAcceleration import TestLoopAcceleration
from test.Reach.TestIntervalUnion import TestIntervalUnion
from test.Reach.TestFullScenarioWithoutParameters import TestFullScenarioWithoutParamters

from test.Equations.TestUnion import TestUnion
from test.Equations.TestAdd import TestAdd
from test.Equations.TestIntersection import TestIntersection
from test.Equations.TestOverlaps import TestOverlaps
from test.Equations.TestNoOverlaps import TestNoOverlaps
from test.Equations.TestFullAnalysis import TestFullAnalysis

if __name__ == '__main__':
    unittest.main()
