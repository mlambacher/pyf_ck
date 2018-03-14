"""
BFAL Generator for MiniPython

This takes a MiniPython program represented using the syntax definitions from structure.py,
and creates BFAL assembly from it.

Marius Lambacher, 2018
"""

from .strucure import *
from .errors import *

class BFALGenerator:
  def __init__(self):
    self.cmds = []

  def generate(self, program):
    if not isinstance(program, Program): raise ProgramInputError()

    self.cmds = []
    self.visit(program)


  def visit(self, obj):
    try:
      if isinstance(obj, Program):
        self.visit(obj.functions)
        self.visit(obj.declarations)
        self.visit(obj.statement)


      elif isinstance(obj, Function): pass

      elif isinstance(obj, Declaration): pass

      elif isinstance(obj, Composite):
        for statement in obj.statements:
          self.visit(statement)

      elif isinstance(obj, Assignment): pass

      elif isinstance(obj, Write):
        self.cmds += 'POP R0'
        self.cmds += 'OUT R0'

      elif isinstance(obj, While): pass

      elif isinstance(obj, IfThen):
        self.visit(obj.cond)

        self.cmds += 'IF'
        self.visit(obj.thenBranch)
        self.cmds += 'ENDIF'

      elif isinstance(obj, IfThenElse): pass

      elif isinstance(obj, Return): pass

      elif isinstance(obj, Number):
        val = obj.value
        if val < 0 or val > 255: raise NumberValError()

        self.cmds += 'PUSH {}'.format(val)


      elif isinstance(obj, Variable): pass

      elif isinstance(obj, Read):
        self.cmds += 'INP R0'
        self.cmds += 'PUSH R0'

      elif isinstance(obj, Binary):
        self.visit(obj.lhs)
        self.visit(obj.rhs)

        op = obj.operator
        if not op in BINOPS: raise UnknownBinopError()

        self.cmds += 'POP R0'
        self.cmds += 'POP R1'

        if   op == 'ADD': self.cmds += 'ADD R2 R0 R1'
        elif op == 'SUB': self.cmds += 'SUB R2 R0 R1'
        elif op == 'MUL': self.cmds += 'MUL R2 R0 R1'
        elif op == 'DIV': self.cmds += 'DIV R2 R0 R1'

        self.cmds += 'PUSH R2'


      elif isinstance(obj, Call): pass

      elif isinstance(obj, CTrue): self.cmds += 'TRUE'

      elif isinstance(obj, CFalse): self.cmds += 'FALSE'

      elif isinstance(obj, UnaryCondition):
        self.visit(obj.operand)

        op = obj.operator
        if not op in CUNOPS: raise UnknownCunopError()

        if op == 'NOT': self.cmds += 'NOT'

      #elif isinstance(obj, BinaryCondition): pass

      elif isinstance(obj, Comparison):
        self.visit(obj.lhs)
        self.visit(obj.rhs)

        op = obj.operator
        if not op in COMPARISONS: raise UnknownComparisonError()

        self.cmds += 'POP R0'
        self.cmds += 'POP R1'

        if op == 'EQ': self.cmds += 'EQ R0 R1'
        if op == 'NE': self.cmds += 'NE R0 R1'
        if op == 'LE': self.cmds += 'LE R0 R1'
        if op == 'LT': self.cmds += 'LT R0 R1'
        if op == 'GE': self.cmds += 'GE R0 R1'
        if op == 'GT': self.cmds += 'GT R0 R1'

        self.cmds += 'PUSH R2'

      else: raise ObjTypeError()


    except (BFALGenerationError, Exception) as err:
      if isinstance(err, BFALGenerationError): msg = 'Bad news, an internal error occured'
      else: msg = 'Very bad news, a runtime error occured'

      msg += ' while visiting a "{}" object:\n\t'.format(obj)
      print(msg)
      raise err