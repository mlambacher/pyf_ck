class InternalError(RuntimeError):
  """Internal error of the parser; those should not occur"""

class UnknownOpcodeError(InternalError):
  """An unknown opcode was observed while parsing"""

class UnknownCmdTypeError(InternalError):
  """An unknown command type was determined while parsing"""

class UnknownCmdClassError(InternalError):
  """An unknown command class was determined while parsing"""

class ErrorDetectionError(InternalError):
  """Unable to detect error in assembly"""

class ComparisonMacroModeError(InternalError):
  """Unable to determine mode for comparison macro"""

class ComparisonMacroTypeError(InternalError):
  """Unable to determine type for comparison macro"""


class AssemblyError(Exception):
  """Error in the assembly code, clones basic Python errors"""
  def __init__(self, *args, name='GeneralError'):
    Exception.__init__(self, *args)
    self.name = name

class AssemblyNameError(AssemblyError):
  def __init__(self, *args):
    AssemblyError.__init__(self, *args, name='NameError')

class AssemblyValueError(AssemblyError):
  def __init__(self, *args):
    AssemblyError.__init__(self, *args, name='ValueError')

class AssemblyTypeError(AssemblyError):
  def __init__(self, *args):
    AssemblyError.__init__(self, *args, name='TypeError')

class AssemblySyntaxError(AssemblyError):
  def __init__(self, *args):
    AssemblyError.__init__(self, *args, name='SyntaxError')
