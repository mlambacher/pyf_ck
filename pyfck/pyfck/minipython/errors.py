"""
Custom errors to be used by the MiniPython tools

Marius Lambacher, 2018
"""

class BFALGenerationError(RuntimeError):
  """Internal error of the assembly generator; those should not occur"""

  def __init__(self, msg=''):
    RuntimeError.__init__(self, '{}: {}'.format(self.__doc__, msg))


class ProgramInputError(BFALGenerationError):
  """generate() must be called with a structure.Program instance"""

class ObjTypeError(BFALGenerationError):
  """The Generator tried to visit a object of unknown type"""

class NumberValError(BFALGenerationError):
  """The value of a number has to be in range 0-255"""

class UnknownBinopError(BFALGenerationError):
  """The Generator encountered an unknown binary operator"""

class UnknownCunopError(BFALGenerationError):
  """The Generator encountered an unknown unary condition operator"""

class UnknownComparisonError(BFALGenerationError):
  """The Generator encountered an unknown comparison operator"""