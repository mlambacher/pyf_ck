"""
Tests for the bfInterpreter module

Marius Lambacher, 2017
"""

import unittest
from unittest.mock import patch

from ..bfInterpreter import Interpreter
import numpy as np
from io import StringIO

class TestBFInterpreter(unittest.TestCase):
  def setUp(self):
    self.interpreter = Interpreter()

  def runCmds(self, cmds):
    self.interpreter.load(cmds)
    self.interpreter.run()

  def test_bfInterpreter_load_basic(self):
    self.interpreter.load('+-FO0<>')
    np.testing.assert_array_equal(self.interpreter.cmds, np.array(['+', '-', '<', '>'], dtype='U1'))

  def test_bfInterpreter_load_empty(self):
    self.interpreter.load('')
    np.testing.assert_array_equal(self.interpreter.cmds, np.array([], dtype='U1'))

  def test_bfInterpreter_load_optimise_stz(self):
    self.interpreter.load('+>[-]<')
    np.testing.assert_array_equal(self.interpreter.cmds, np.array(['+', '>', '0', '<'], dtype='U1'))

  def test_bfInterpreter_init_basics(self):
    self.interpreter.load('+-FO0<>')
    self.interpreter.init()
    self.assertEqual(self.interpreter.cmdPtr, 0)

  def test_bfInterpreter_init_jumps(self):
    self.interpreter.load('++[>+>+<[-<+>]<]')
    self.interpreter.init()
    np.testing.assert_array_equal(self.interpreter.jmps, np.array([0, 0, 16, 0, 0, 0, 0, 0, 14, 0, 0, 0, 0, 9, 0, 3], dtype='u4'))

  def test_bfInterpreter_init_memory(self):
    interpreter = Interpreter(memorySize=12345)
    interpreter.load('')
    interpreter.init()
    self.assertEqual(interpreter.memorySize, 12345)
    np.testing.assert_array_equal(interpreter.memory, np.zeros(12345, dtype='u8'))


  def test_bfInterpreter_run_empty(self):
    self.runCmds('')
    self.assertEqual(self.interpreter.running, False)

  def test_bfInterpreter_run_debug(self):
    self.interpreter.setDebugging(True)

    self.runCmds('')
    self.assertEqual(self.interpreter.running, True)

    self.interpreter.step()
    self.assertEqual(self.interpreter.running, False)

    self.interpreter.setDebugging(False)

  def test_bfInterpreter_cmd_mvl(self):
    self.runCmds('>>>>')
    self.assertEqual(self.interpreter.memoryPtr, 4)

  def test_bfInterpreter_cmd_mvr(self):
    self.runCmds('>>>><<')
    self.assertEqual(self.interpreter.memoryPtr, 2)

  def test_bfInterpreter_cmd_mvr_outOfBounds(self):
    with self.assertRaisesRegex(MemoryError, 'Forbidden memory'):
      self.runCmds('<')

  def test_bfInterpreter_cmd_mvl_outOfBounds(self):
    interpreter = Interpreter(memorySize=8)
    interpreter.load('>'*7)
    interpreter.run()       # check that there are at least 8 cells

    interpreter.load('>'*8)
    with self.assertRaisesRegex(MemoryError, 'Forbidden memory'):
      interpreter.run()

  def test_bfInterpreter_cmd_inc(self):
    self.runCmds('+++')
    self.assertEqual(self.interpreter.memory[0], 3)

  def test_bfInterpreter_cmd_dec(self):
    self.runCmds('+++++---')
    self.assertEqual(self.interpreter.memory[0], 2)

  def test_bfInterpreter_memory_wrapping(self):
    self.runCmds('+'*257)
    self.assertEqual(self.interpreter.memory[0], 1)

    self.runCmds('---')
    self.assertEqual(self.interpreter.memory[0], 253)

  def test_bfInterpreter_cmd_loop(self):
    self.runCmds('++++[->+<]')
    self.assertEqual(self.interpreter.memory[0], 0)
    self.assertEqual(self.interpreter.memory[1], 4)

  @patch('sys.stdout', new_callable=StringIO)
  def test_bfInterpreter_cmd_out(self, mock_stdout):
    self.runCmds('.'.join(('+'*65, '+'*32, '-'*87, '+'*38, '+'*180, '')))
    self.assertEqual(mock_stdout.getvalue().strip(), 'Aa\n0ä')

  @patch('sys.stdin', new_callable=StringIO)
  def test_bfInterpreter_cmd_inp_noBuffer(self, mock_stdin):
    interpreter = Interpreter(bufferInput=False)
    mock_stdin.write('Bb\n\n')
    mock_stdin.seek(0)

    interpreter.load(',[>,]')
    interpreter.run()
    np.testing.assert_array_equal(interpreter.memory[0:3], np.array([66, 0, 0], dtype='u1'))

  @patch('sys.stdin', new_callable=StringIO)
  def test_bfInterpreter_cmd_inp_buffer(self, mock_stdin):
    interpreter = Interpreter(bufferInput=True)
    mock_stdin.write('Bb\n1ö\n\n')
    mock_stdin.seek(0)

    interpreter.load(',[>,]')
    interpreter.run()
    np.testing.assert_array_equal(interpreter.memory[0:7], np.array([66, 98, 10, 49, 246, 10, 0], dtype='u8'))


