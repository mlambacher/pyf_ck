"""
Tests for utilities

Marius Lambacher, 2017
"""

import unittest
from unittest.mock import patch

from .. import util

class TestUtils(unittest.TestCase):
  def test_litStrToInt_bin(self):
    self.assertEqual(util.litStrToInt('0b1'), 0b1)
    self.assertEqual(util.litStrToInt('0B1011'), 0b1011)

  def test_litStrToInt_oct(self):
    self.assertEqual(util.litStrToInt('0o4'), 0o4)
    self.assertEqual(util.litStrToInt('0O123'), 0o123)

  def test_litStrToInt_hex(self):
    self.assertEqual(util.litStrToInt('0xA'), 0xA)
    self.assertEqual(util.litStrToInt('0X123'), 0x123)

  def test_litStrToInt_dec(self):
    self.assertEqual(util.litStrToInt('9'), 9)
    self.assertEqual(util.litStrToInt('123'), 123)

  def test_litStrToInt_errors(self):
    with self.assertRaises(ValueError): util.litStrToInt('0b2')
    with self.assertRaises(ValueError): util.litStrToInt('0o9')
    with self.assertRaises(ValueError): util.litStrToInt('0xR')
    with self.assertRaises(ValueError): util.litStrToInt('W')