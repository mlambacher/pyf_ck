"""
Tests for the bfInterpreter module

Marius Lambacher, 2017
"""

import unittest
from ..bfaltools.bfInterpreter import Interpreter
import numpy as np

class TestBFInterpreter(unittest.TestCase):
  def setUp(self):
    pass

  def test_bfInterpreter_loadSource(self):
    interp = Interpreter()
    interp.load("+-FO0<>")

    self.assertEqual(interp.cmds, np.array(['+', '-', '<', '>'], dtype='U1'))

  def test_bfInterpreter_initFunction(self):
    interp = Interpreter()
    interp.load("+-FO0<>")

    self.assertEqual(interp.cmds, np.array(['+', '-', '<', '>'], dtype='U1'))
