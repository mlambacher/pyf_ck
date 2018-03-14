"""
MiniPython definitions

These definitions represent the minipython syntax

MiniPython is a minimalistic high level language derived from minijava, with the goal of creating a more pythonic syntax.

Marius Lambacher, 2018
"""


# UNOPS = ('ADD', 'SUB')
BINOPS = ('ADD', 'SUB', 'MUL', 'DIV') #, 'MOD')

CUNOPS = ('NOT',)
CBINOPS = ('AND', 'OR')

COMPARISONS = ('EQ', 'NE', 'LE', 'LT', 'GE', 'GT')


class SyntaxElement:
  def __str__(self):
    return str(self.__class__).split("'")[1].split('.')[1]

class Program(SyntaxElement):
  def __init__(self, functions, declarations, statement):
    self.functions = functions
    self.declarations = declarations
    self.statement = statement


class Function(SyntaxElement):
  def __init__(self, name, parameters, declarations, statement):
    self.name = name
    self.parameters = parameters
    self.declarations = declarations
    self.statement = statement



class Declaration(SyntaxElement):
  def __init__(self, names):
    self.names = names



class Statement(SyntaxElement): pass

class Composite(Statement):
  def __init__(self, statements):
    self.statements = statements

class Assignment(Statement):
  def __init__(self, name, expression):
    self.name = name
    self.expression = expression

class Write(Statement):
  def __init__(self, expression):
    self.expression = expression

class While(Statement):
  def __init__(self, cond, body):
    self.cond = cond
    self.body = body

class IfThen(Statement):
  def __init__(self, cond, thenBranch):
    self.cond = cond
    self.thenBranch = thenBranch

class IfThenElse(Statement):
  def __init__(self, cond, thenBranch, elseBranch):
    self.cond = cond
    self.thenBranch = thenBranch
    self.elseBranch = elseBranch

class Return(Statement):
  def __init__(self, expression):
    self.expression = expression




class Expression(SyntaxElement): pass

class Number(Expression):
  def __init__(self, value):
    self.value = value

class Variable(Expression):
  def __init__(self, name):
    self.name = name

class Read(Expression):
  def __init__(self, name):
    self.name = name

# class Unary(Expression):
#   def __init__(self, operator, operand):
#     self.operator = operator
#     self.operand = operand

class Binary(Expression):
  def __init__(self, lhs, operator, rhs):
    self.lhs = lhs
    self.operator = operator
    self.rhs = rhs

class Call(Expression):
  def __init__(self, functionName, arguments):
    self.functionName = functionName
    self.arguments = arguments




class Condition(SyntaxElement): pass

class CTrue(Condition): pass
class CFalse(Condition): pass

class UnaryCondition(Condition):
  def __init__(self, operator, operand):
    self.operator = operator
    self.operand = operand

class BinaryCondition(Condition):
  def __init__(self, lhs, operator, rhs):
    self.lhs = lhs
    self.operator = operator
    self.rhs = rhs


class Comparison(Condition):
  def __init__(self, lhs, operator, rhs):
    self.lhs = lhs
    self.operator = operator
    self.rhs = rhs

