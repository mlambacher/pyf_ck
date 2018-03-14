"""
Custom errors to be used by the bfalParser

Marius Lambacher, 2018
"""

class InternalError(RuntimeError):
  """Internal error of the parser; those should not occur"""

  def __init__(self, msg=''):
    RuntimeError.__init__(self, '{}: {}'.format(self.__doc__, msg))


class ConstantsError(InternalError):
  """An unknown constant was encountered"""

class UnknownOpcodeError(InternalError):
  """An unknown opcode was observed """

class UnknownCmdTypeError(InternalError):
  """An unknown command type was determined"""

class UnknownCmdClassError(InternalError):
  """An unknown command class was determined"""

class ErrorDetectionError(InternalError):
  """Unable to detect error in assembly"""

class RepeatMacroRepeatsError(InternalError):
  """Trying to repeat a negative number of times"""

class ComparisonMacroModeError(InternalError):
  """Unable to determine mode for comparison macro"""

class ComparisonMacroTypeError(InternalError):
  """Unable to determine type for comparison macro"""

class MulMacroTypeError(InternalError):
  """Unable to determine type for mul macro"""

class DivMacroTypeError(InternalError):
  """Unable to determine type for div macro"""


# class InternalWarning(Warning):
#   """Internal warning of the parser"""
#
#   def __init__(self, msg=''):
#     Warning.__init__(self, '{}: {}'.format(self.__doc__, msg))
#
#
# class PostProcessWarning(InternalWarning):
#   """PostProcess() did code cleanup, should not happen"""



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

