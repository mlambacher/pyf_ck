import unittest
from .tests import *

TestSuite = unittest.TestSuite()
TestSuite.addTest(test_bfInterpreter.TestBFInterpreter)
TestSuite.addTest(test_bfParser.TestBFALParser)
TestSuite.addTest(test_opcodes.TestOpcodes)
TestSuite.addTest(test_util.TestUtils)
