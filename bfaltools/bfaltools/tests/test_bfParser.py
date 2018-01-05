"""
Tests for the bfalParser module

They test general functionality, independent of the opcodes & memory layout

Marius Lambacher, 2017
"""


import unittest
from unittest.mock import patch

from ..bfalParser import Parser
from..bfalParser.errors import *
from . import dummyOpcodes
from . import dummyMemoryLayout
import numpy as np
from io import StringIO
import sys


class DummyParser(Parser):
  def __init__(self):
    Parser.__init__(self)

    self.OPCODE_CLASSES = dummyOpcodes.OPCODE_CLASSES
    self.OPCODES = dummyOpcodes.OPCODES
    self.OPCODE_IDENTIFIERS = dummyOpcodes.OPCODE_IDENTIFIERS
    self.OPCODE_TYPES = dummyOpcodes.OPCODE_TYPES

    #self.CONDITIONS = dummyOpcodes.CONDITIONS
    #self.CONDITION_IDENTIFIERS = dummyOpcodes.CONDITION_IDENTIFIERS
    #self.CONDITION_TYPES = dummyOpcodes.CONDITION_TYPES

    self.REGISTERS = dummyMemoryLayout.REGISTERS
    self.TEMPS = dummyMemoryLayout.TEMPS
    self.START_POS = dummyMemoryLayout.START_POS




class TestBFALParser(unittest.TestCase):
  def setUp(self):
    self.parser = DummyParser()



  def test_bfalParser_parseCmdParts_basic(self):
    self.assertEqual(self.parser.parseCmdParts('Foo BAR  baz\tblubb'), ['FOO', 'BAR', 'BAZ', 'BLUBB'])

  def test_bfalParser_parseCmdParts_blocks_basicOperation(self):
    self.assertEqual(self.parser.parseCmdParts('Foo BAR  "Hello World\t!""baz" baz'), ['FOO', 'BAR', 'Hello World\t!', 'baz', 'BAZ'])

  def test_bfalParser_parseCmdParts_blocks_quotationError(self):
    with self.assertRaisesRegex(AssemblySyntaxError, "Quotation"):
      self.parser.parseCmdParts('"Foo""Bar baz')


  def test_bfalParser_parseOpcode_basicOperation(self):
    res = self.parser.parseOpcode(('YYY', 'foo', 'bar'))
    self.assertEqual(res, (dummyOpcodes.OPCODES.OPY, dummyOpcodes.OPCODE_CLASSES.INSTRUCTION, ('R', 'RV')))

  def test_bfalParser_parseOpcode_unknownOpcodeError(self):
    with self.assertRaisesRegex(AssemblyNameError, 'Unknown'):
      self.parser.parseOpcode(('foo', 'bar'))



  def test_bfalParser_parseArg_basicOperation(self):
    #resC = self.parser.parseArg(None, 'CONDU')
    resR = self.parser.parseArg(None, 'R3')
    resV = self.parser.parseArg(None, '0xFF')
    resT = self.parser.parseArg(None, 'FOOBAR')

    #self.assertEqual(resC, ('C', dummyOpcodes.CONDITIONS.CU))
    self.assertEqual(resR, ('R', 'R3'))
    self.assertEqual(resV, ('V', str(0xFF)))
    self.assertEqual(resT, ('T', 'FOOBAR'))


  def test_bfalParser_parseArg_alias(self):
    with patch.dict(self.parser.ALIASES, {'foo': '123'}):
      resA = self.parser.parseArg(None, 'foo')
      resNA = self.parser.parseArg(dummyOpcodes.OPCODES.ALIAS, 'foo')

    self.assertEqual(resA, ('V', '123'))
    self.assertEqual(resNA, ('T', 'foo'))


  def test_bfalParser_findError_numArguments(self):
    with self.assertRaisesRegex(AssemblyTypeError, 'argument.*must be 1'):
      self.parser.findError('VV', self.parser.OPCODE_TYPES[self.parser.OPCODES.OPX][1], [])

    with self.assertRaisesRegex(AssemblyTypeError, 'argument.*must be in \[2, 3\]'):
      self.parser.findError('R', self.parser.OPCODE_TYPES[self.parser.OPCODES.OPZ][1], [])


  def test_bfalParser_findError_typeArguments(self):
    with self.assertRaisesRegex(AssemblyNameError, 'argument.*1.*foo.*not.*register'):
      self.parser.findError('V', self.parser.OPCODE_TYPES[self.parser.OPCODES.OPX][1], ['foo', None, None])

    with self.assertRaisesRegex(AssemblyError, 'argument.*2.*bar.*not.*value'):
      self.parser.findError('RRV', self.parser.OPCODE_TYPES[self.parser.OPCODES.OPZ][1], ['foo', 'bar', '42'])


  def test_bfalParser_parseCommand(self):
    self.assertEqual(self.parser.parseCommand('YYY R0 42'), (self.parser.OPCODE_CLASSES.INSTRUCTION, self.parser.OPCODES.OPY, 'RV', ['R0', '42', None]))
