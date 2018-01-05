"""
Tests for the individual opcodes

Separated from general tests of bfParser, so those can be independent of opcodes

Marius Lambacher, 2017
"""


from unittest import TestCase, skip
from unittest.mock import patch

import itertools

from ..bfalParser import Parser
from ..bfInterpreter import Interpreter
from . import dummyOpcodes
from . import dummyMemoryLayout
import numpy as np
from io import StringIO
import sys
import re


class TestOpcodes(TestCase):
  def setUp(self):
    self.memorySize = 30000

    self.parser = Parser()
    self.interpreter = Interpreter(memorySize=self.memorySize)#debugging=True)



  def loadBfal(self, cmds):
    """Compile and load code into self.interpreter"""
    self.interpreter.load(self.parser.compile(cmds))

  def runBfal(self, cmds, memory=None):
    """Runs given code in self.interpreter. If memory is given, it is copied into the interpreter.memory"""
    self.loadBfal(cmds)
    if memory is None:
      self.interpreter.run()

    else:
      self.interpreter.init()
      self.interpreter.memory = memory.copy()
      self.noInitRun()


  def noInitRun(self):
    """Run the interpreter without initialisation"""
    self.interpreter.running = True
    while self.interpreter.running:
      self.interpreter._step()

  def getCell(self, cell, memory=None):
    """Syntactic sugar for getting a cell by its name; if memory is None, use self.interpreter.memory"""

    if memory is None: memory = self.interpreter.memory
    return memory[self.parser.CELLS.index(cell)]

  def setCell(self, cell, value, memory=None):
    """Syntactic sugar for setting a cell by its name; if memory is None, use self.interpreter.memory"""

    if memory is None: memory = self.interpreter.memory
    memory[self.parser.CELLS.index(cell)] = value


  def atTestRegisters(self, nDim=1, nRegs=4, resetCount=False):
    """Decorator, call test for each combination of ndim (out of nRegs) testRegisters, passed to it via 'reg' or 'reg[0-(nDim-1)]'"""

    def testDecorator(test):
      def testDecorated(self, **kwargs):
        testRegisters = [self.parser.REGISTERS[0], self.parser.REGISTERS[1], self.parser.REGISTERS[7], self.parser.REGISTERS[3],
                         self.parser.REGISTERS[2], self.parser.REGISTERS[5], self.parser.REGISTERS[4], self.parser.REGISTERS[6]]
        testRegisters = testRegisters[:nRegs]

        combinations = itertools.product(testRegisters, repeat=nDim)
        argNames = ['reg{}'.format(i) for i in range(nDim)]
        for c in combinations:
          key = 'TestCount_for_{}'.format(test.__name__)
          if key in self.__dict__: self.__dict__[key] = 0

          if nDim == 1: regArgs = {'reg': c[0]}
          else: regArgs = dict(zip(argNames, c))
          #print(test.__name__, regArgs)
          test(self, **regArgs, **kwargs)

      return testDecorated
    return testDecorator


  def withTestValues(self, *expr):
    """Decorator, run test with a test value, passed to test via 'val' or 'val[0-(ndim-1)]'
    expr: expression the values are generated from, called with a running count, passed via 'val'
            if multiple, a value is generated for each expression in the iterable"""

    def testDecorator(test):
      def testDecorated(self, **kwargs):
        key = 'TestCount_for_{}'.format(test.__name__)
        if not key in self.__dict__: self.__dict__[key] = 0
        else: self.__dict__[key] += 1

        valArgs = {}
        if len(expr) > 1:
          for i, e in enumerate(expr):
            valArgs['val{}'.format(i)] = e(self.__dict__[key])

        else:
          valArgs['val'] = expr[0](self.__dict__[key])

        test(self, **valArgs, **kwargs)

      return testDecorated
    return testDecorator


  def runNTimes(self, n):
    """Decorator, run test n times (e.g. for use in combination with @self.withTestValues)"""

    def testDecorator(test):
      def testDecorated(self, **kwargs):
        for i in range(n):
          test(self, **kwargs)

      return testDecorated
    return testDecorator



  def skipEqualRegisters(self, *positions):
    """Skip test if registers are equal
    positions (if given) are register argument indices; if they are equal, they are skipped
    if not given, the test is skipped if all given registers are equal"""

    def testDecorator(test):
      def testDecorated(self, **kwargs):
        regs = []
        if len(positions):
          for p in positions: regs.append(kwargs['reg{}'.format(p)])

        else:
          for i in range(3):    # maximum number of arguments
            name = 'reg{}'.format(i)
            if name in kwargs: regs.append(kwargs[name])
            else: break

        if regs.count(regs[0]) != len(regs): test(self, **kwargs)

      return testDecorated
    return testDecorator



  def zerosTest(self, test, rc=0,**kwargs):
    """test with memory set to 0s; the condition register can be set independently"""
    memory = np.zeros(self.memorySize, dtype='u1')
    self.setCell('RC', rc, memory)
    test(self, memory=memory, **kwargs)

  def nonzerosTest(self, test, rc=0, **kwargs):
    """set with registers containing nonzero values; the condition register can be set independently"""
    memory = np.zeros(self.memorySize, dtype='u1')
    self.setCell('RC', rc, memory)
    for reg in self.parser.REGISTERS:
      i = self.parser.CELLS.index(reg)
      val = i*13+5
      if i % 2: val = ~val
      memory[i] = val

    test(self, memory=memory, **kwargs)


  def generateMemoryChange(self, memory, reg, val=None, expr=None):
    """Copy memory and return with register either changed to val or to expr(old register value)"""

    if ((val is not None) and (expr is not None)) or ((val is None) and (expr is None)):
      raise NameError('Either value or expr should be given, not both nor neither!')

    m = memory.copy()
    if val is not None: self.setCell(reg, val, m)
    else: self.setCell(reg, expr(self.getCell(reg, m)), m)

    return m


  def assertRegisterEqual(self, memory, reg, val=None, expr=None):
    """Assert two things:
        - reg is equal to val if given, or to expr(previous register value) if given
        - rest of memory is unchanged
    """

    np.testing.assert_array_equal(self.interpreter.memory, self.generateMemoryChange(memory, reg, val, expr))

  def assertRegisterNotEqual(self, memory, reg, val=None, expr=None):
    """Assert two things:
        - reg is not equal to val if given, or to expr(previous register value) if given
        - rest of memory is unchanged
    """

    cm = self.generateMemoryChange(memory, reg, val, expr)
    im = self.interpreter.memory
    i = self.parser.CELLS.index(reg)
    np.testing.assert_array_equal(im[:i], cm[:i])
    np.testing.assert_array_equal(im[i+1:], cm[i+1:])
    self.assertNotEqual(im[i], cm[i])



  def test_opcodes_allImplemented(self):
    keys = self.__class__.__dict__.keys()
    for opc in self.parser.OPCODES:
      for t in self.parser.OPCODE_TYPES[opc][1]:
        if t == '': name = opc.name
        else: name = '{}_{}'.format(opc.name, t.upper())

        r = re.compile('.*{}'.format(name))
        for k in keys:
          if r.match(k): break

        else: self.fail('Test for {} not implemented'.format(name))



  def test_opcodes_SET_RV(self):
    @self.atTestRegisters()
    @self.withTestValues(lambda i: i**2)
    def test(self, memory, reg, val):
      self.runBfal('SET {} {}'.format(reg, val), memory)
      self.assertRegisterEqual(memory, reg, val=val)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_SET_RR(self):
    @self.atTestRegisters(nDim=2)
    @self.withTestValues(lambda i: i**2)
    def test(self, memory, reg0, reg1, val):
      m = memory.copy()
      self.setCell(reg1, val, m)
      self.runBfal('SET {} {}'.format(reg0, reg1), m)
      self.assertRegisterEqual(m, reg0, val=val)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_STZ_R(self):
    @self.atTestRegisters()
    def test(self, memory, reg):
      self.runBfal('STZ {}'.format(reg), memory)
      self.assertRegisterEqual(memory, reg, val=0)

    self.nonzerosTest(test)


  def test_opcodes_INC_R(self):
    @self.atTestRegisters()
    def test(self, memory, reg):
      self.runBfal('INC {}'.format(reg), memory)
      self.assertRegisterEqual(memory, reg, expr=lambda v: v + 1)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_INC_RV(self):
    @self.atTestRegisters()
    @self.withTestValues(lambda i: i**2)
    def test(self, memory, reg, val):
      self.runBfal('INC {} {}'.format(reg, val), memory)
      self.assertRegisterEqual(memory, reg, expr=lambda v: v + val)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_INC_RR(self):
    @self.atTestRegisters(nDim=2)
    @self.withTestValues(lambda i: i**2)
    @self.skipEqualRegisters()
    def test(self, memory, reg0, reg1, val):
      m = memory.copy()
      self.setCell(reg1, val, m)
      self.runBfal('INC {} {}'.format(reg0, reg1), m)
      self.assertRegisterEqual(m, reg0, expr=lambda v: v+val)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_DEC_R(self):
    @self.atTestRegisters()
    def test(self, memory, reg):
      self.runBfal('DEC {}'.format(reg), memory)
      self.assertRegisterEqual(memory, reg, expr=lambda v: v-1)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_DEC_RV(self):
    @self.atTestRegisters()
    @self.withTestValues(lambda i: i**2)
    def test(self, memory, reg, val):
      self.runBfal('DEC {} {}'.format(reg, val), memory)
      self.assertRegisterEqual(memory, reg, expr=lambda v: v-val)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_DEC_RR(self):
    @self.atTestRegisters(nDim=2)
    @self.withTestValues(lambda i: i**2)
    @self.skipEqualRegisters()
    def test(self, memory, reg0, reg1, val):
      m = memory.copy()
      self.setCell(reg1, val, m)
      self.runBfal('DEC {} {}'.format(reg0, reg1), m)
      self.assertRegisterEqual(m, reg0, expr=lambda v: v-val)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_ADD_RRV(self):
    @self.atTestRegisters(nDim=2)
    @self.withTestValues(lambda i: i**2, lambda j: j**2+2)
    def test(self, memory, reg0, reg1, val0, val1):
      m = memory.copy()
      self.setCell(reg1, val0, m)
      self.runBfal('ADD {} {} {}'.format(reg0, reg1, val1), m)
      self.assertRegisterEqual(m, reg0, val=val0+val1)

    self.zerosTest(test)
    self.nonzerosTest(test)

  def test_opcodes_ADD_RRR(self):
    @self.atTestRegisters(nDim=3, nRegs=3)
    @self.withTestValues(lambda i: i**2, lambda j: j**2+2)
    @self.skipEqualRegisters(0, 2)
    def test(self, memory, reg0, reg1, reg2, val0, val1):
      if reg1 == reg2: val1 = val0

      m = memory.copy()
      self.setCell(reg1, val0, m)
      self.setCell(reg2, val1, m)
      self.runBfal('ADD {} {} {}'.format(reg0, reg1, reg2), m)
      self.assertRegisterEqual(m, reg0, val=val0+val1)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_SUB_RRV(self):
    @self.atTestRegisters(nDim=2)
    @self.withTestValues(lambda i: i**2, lambda j: j**2+2)
    def test(self, memory, reg0, reg1, val0, val1):
      m = memory.copy()
      self.setCell(reg1, val0, m)
      self.runBfal('SUB {} {} {}'.format(reg0, reg1, val1), m)
      self.assertRegisterEqual(m, reg0, val=val0-val1)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_SUB_RRR(self):
    @self.atTestRegisters(nDim=3, nRegs=3)
    @self.withTestValues(lambda i: i**2, lambda j: j**2+2)
    @self.skipEqualRegisters(0, 2)
    def test(self, memory, reg0, reg1, reg2, val0, val1):
      if reg1 == reg2: val1 = val0
      m = memory.copy()
      self.setCell(reg1, val0, m)
      self.setCell(reg2, val1, m)
      self.runBfal('SUB {} {} {}'.format(reg0, reg1, reg2), m)
      self.assertRegisterEqual(m, reg0, val=val0-val1)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_TRUE(self):
    def test(self, memory):
      self.runBfal('TRUE', memory)
      self.assertRegisterNotEqual(memory, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_FALSE(self):
    def test(self, memory):
      self.runBfal('FALSE', memory)
      self.assertRegisterEqual(memory, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_NOT_ZERO_V(self):
    @self.runNTimes(2)
    @self.withTestValues(lambda i: 42*(i%2))
    def test(self, memory, val):
      self.runBfal('NZR {}'.format(val), memory)
      if val == 0: self.assertRegisterEqual(memory, 'RC', val=0)
      else: self.assertRegisterNotEqual(memory, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_NOT_ZERO_R(self):
    @self.atTestRegisters(resetCount=True)
    @self.runNTimes(2)
    @self.withTestValues(lambda i: 42*(i%2))
    def test(self, memory, reg, val):
      m = memory.copy()
      self.setCell(reg, val, m)
      self.runBfal('NZR {}'.format(val), m)
      if val == 0: self.assertRegisterEqual(m, 'RC', val=0)
      else: self.assertRegisterNotEqual(m, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_NOT_EQUAL_VV(self):
    @self.runNTimes(4)
    @self.withTestValues(lambda i: i, lambda j: (j**2)//2)
    def test(self, memory, val0, val1):
      self.runBfal('NEQ {} {}'.format(val0, val1), memory)
      if val0 == val1: self.assertRegisterEqual(memory, 'RC', val=0)
      else: self.assertRegisterNotEqual(memory, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_NOT_EQUAL_RV(self):
    @self.atTestRegisters(resetCount=True)
    @self.runNTimes(4)
    @self.withTestValues(lambda i: i, lambda j: (j**2)//2)
    def test(self, memory, reg, val0, val1):
      m = memory.copy()
      self.setCell(reg, val0, m)
      self.runBfal('NEQ {} {}'.format(reg, val1), m)
      if val0 == val1: self.assertRegisterEqual(m, 'RC', val=0)
      else: self.assertRegisterNotEqual(m, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)

  def test_opcodes_NOT_EQUAL_RR(self):
    @self.atTestRegisters(nDim=2, nRegs=3, resetCount=True)
    @self.runNTimes(3)
    @self.withTestValues(lambda i: i+1, lambda j: ((j+1)**2)//2)
    def test(self, memory, reg0, reg1, val0, val1):
      m = memory.copy()
      self.setCell(reg0, val0, m)
      self.setCell(reg1, val1, m)
      self.runBfal('NEQ {} {}'.format(reg0, reg1), m)
      if (reg0 == reg1) or (val0 == val1): self.assertRegisterEqual(m, 'RC', val=0)
      else: self.assertRegisterNotEqual(m, 'RC', val=0)

    self.zerosTest(test)
    self.zerosTest(test, rc=1)
    self.nonzerosTest(test)


  @patch('sys.stdin', new_callable=StringIO)
  def test_opcodes_INPUT_R(self, mock_stdin):
    @self.atTestRegisters()
    def test(self, mock_stdin, memory, reg):
      string = 'B1ö'
      mock_stdin.write(string)

      for i, c in enumerate(string):
        mock_stdin.seek(i)
        self.runBfal('INP {}'.format(reg), memory)

        m = memory.copy()
        self.setCell(reg, ord(c), m)
        np.testing.assert_array_equal(self.interpreter.memory, m)

    self.zerosTest(test, mock_stdin=mock_stdin)
    self.nonzerosTest(test, mock_stdin=mock_stdin)


  @patch('sys.stdout', new_callable=StringIO)
  def test_opcodes_OUTPUT_R(self, mock_stdout):
    @self.atTestRegisters()
    def test(self, mock_stdout, memory, reg):
      string = 'A0ä'
      mock_stdout.seek(0)

      for c in string:
        m = memory.copy()
        self.setCell(reg, ord(c), m)
        self.runBfal('OUT {}'.format(reg), m)

      self.assertEqual(mock_stdout.getvalue().strip(), string)

    self.zerosTest(test, mock_stdout=mock_stdout)
    self.nonzerosTest(test, mock_stdout=mock_stdout)



  def test_opcodes_LOOP(self):
    @self.atTestRegisters(nDim=2, nRegs=3)
    @self.skipEqualRegisters()
    @self.withTestValues(lambda i: i*3)
    def test(self, memory, reg0, reg1, val):
      m = memory.copy()
      self.setCell(reg0, val, m)
      self.runBfal('STZ {1}\nNZR {0}\nLOOP\nDEC {0}\nINC {1}\nNZR {0}\nENDLOOP'.format(reg0, reg1), m)
      self.setCell(reg0, 0, m)
      self.assertRegisterEqual(m, reg1, val=val)

    self.zerosTest(test)
    self.nonzerosTest(test)


  def test_opcodes_IF(self):
    @self.atTestRegisters(nDim=2, nRegs=3)
    @self.skipEqualRegisters()
    @self.withTestValues(lambda i: i*3)
    def test(self, memory, reg0, reg1, val):
      m = memory.copy()
      self.setCell(reg0, val, m)
      self.runBfal('SET {1} 42\nNZR {0}\nIF\nDEC {0}\nINC {1}\nENDIF'.format(reg0, reg1), m)
      self.setCell(reg1, 42, m)

      res = 42
      if val != 0:
        self.setCell(reg0, val-1, m)
        res = 43

      self.assertRegisterEqual(m, reg1, val=res)

    self.zerosTest(test)
    self.nonzerosTest(test)

  @skip('Already tested in test_opcodes_LOOP')
  def test_opcodes_END_LOOP(self): pass

  @skip('Already tested in test_opcodes_IF')
  def test_opcodes_END_IF(self): pass


  def test_opcodes_ALIAS_TV(self):
    self.parser.compile('ALIAS FOO 42')
    self.assertIn('FOO', self.parser.ALIASES)
    self.assertEqual(self.parser.ALIASES['FOO'], '42')

  def test_opcodes_ALIAS_TR(self):
    self.parser.compile('ALIAS FOO R0')
    self.assertIn('FOO', self.parser.ALIASES)
    self.assertEqual(self.parser.ALIASES['FOO'], 'R0')

  @patch('sys.stdout', new_callable=StringIO)
  def test_opcodes_PRINT_T(self, mock_stdout):
    def test(self, mock_stdout, memory):
      mock_stdout.seek(0)

      string = 'C3ü'
      self.runBfal('PRT "{}"'.format(string), memory)
      self.assertEqual(mock_stdout.getvalue().strip(), string)
      np.testing.assert_array_equal(self.interpreter.memory, memory)


    self.zerosTest(test, mock_stdout=mock_stdout)
    self.nonzerosTest(test, mock_stdout=mock_stdout)

