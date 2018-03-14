'''
Parser for the Brainfuck Assembly Language (BFAL)

The Parser is the main class to convert BFAL code to brainfuck.


Marius Lambacher, 2017
'''
import re
import sys

from ..util import *
from . import macros
from . import memoryLayout
from . import opcodes
from .errors import *



class Parser:
  def __init__(self):
    ###  aliases as defined with the 'ALIAS' command
    self.ALIASES = {}

    self.ensureCompInit = False

    self.OPCODE_CLASSES = opcodes.OPCODE_CLASSES
    self.OPCODES = opcodes.OPCODES
    self.OPCODE_IDENTIFIERS = opcodes.OPCODE_IDENTIFIERS
    self.OPCODE_TYPES = opcodes.OPCODE_TYPES

    self.REGISTERS = memoryLayout.REGISTERS
    self.TEMPS = memoryLayout.TEMPS
    self.CELLS = memoryLayout.CELLS
    self.CONSTANTS = memoryLayout.CONSTANTS
    self.START_POS = memoryLayout.START_POS



  def parseCmdParts(self, cmd):
    '''
    Splits a line of assembly into its parts.
    Splitting occurs at whitespace; though blocks enclosed by quotes (") will be treated as one part.
    Comments beginning with '//' are ignored

    :param cmd: command to split (string)
    :return: list of cmd parts
    '''

    cmd = cmd.split('//')[0]
    if len(cmd) == 0: return []

    if cmd.count('"') % 2 != 0: raise AssemblySyntaxError('Quotation marks must be of even number')
    cmd = cmd.split('"')
    parts = []
    for i, p in enumerate(cmd):
      if p:
        if i % 2 == 0:
          p = p.upper().strip().split()
          parts.extend(p)

        else: parts.append(p)

    return parts



  def parseOpcode(self, cmdParts):
    '''
    takes a list of cmd parts; gathers the opcode and checks whether it is known.
    :param cmdParts: list of cmd parts
    :return: the retreived opcode, command class and type
    '''

    opcodeId = cmdParts[0]

    if opcodeId not in self.OPCODE_IDENTIFIERS: raise AssemblyNameError('Unknown opcode {}'.format(opcodeId))

    opcode = self.OPCODE_IDENTIFIERS[opcodeId]
    cmdClass, cmdType = self.OPCODE_TYPES[opcode]
    return opcode, cmdClass, cmdType




  def parseArg(self, opcode, arg):
    '''
    Tries to parse an argument for cmdParts
    If the opcode is not the alias opcode, the aliases will be applied here.
    The function will try to determine the type of argument,
    distinguishing between registers ('R'), (int-)values ('V') and text ('T').
    Default is text.

    :param opcode: opcode of current command; used for alias
    :param arg: argument to parse
    :return: type of argument, argument
    '''

    if opcode != self.OPCODES.ALIAS:                       # don't apply the aliases in the alias command, or else they can't be overwritten
      if arg in self.ALIASES.keys(): arg = self.ALIASES[arg]


    if arg in self.REGISTERS:
      argType = 'R'
    else:
      try:
        arg = str(litStrToInt(arg))
        argType = 'V'

      except ValueError: argType = 'T'
    return argType, arg



  def findError(self, type, possibleTypes, args):
    '''
    In case the command parsing detects a wrong type, this function will try to raise a helpful error.
    It will detect a wrong number of arguments and a wrong argument type.

    :param type: type of currrent command
    :param possibleTypes: list of possible types for this command
    :param args: args of the command
    :return: nothing, guaranteed to raise an error
    '''

    length = len(type)
    possibleLengths = []

    for t in possibleTypes:
      if not len(t) in possibleLengths: possibleLengths += [len(t)]

    if not length in possibleLengths:
      if len(possibleLengths) == 1: raise AssemblyTypeError('Wrong number of arguments: {}, must be {}'.format(length, possibleLengths[0]))
      else: raise AssemblyTypeError('Wrong number of arguments: {}, must be in {}'.format(length, sorted(possibleLengths)))
    possibleTypes = [t for t in possibleTypes if len(t)==length]


    for pos in range(length):
      possible = set([t[pos] for t in possibleTypes])
      if not type[pos] in possible:
        break

    else: raise ErrorDetectionError('Unable to find error in arguments')

    errStr = 'Invalid argument {}: \'{}\''.format(pos+1, args[pos])       # pos keeps the position, where break was called
    if len(possible) == 1:
      if 'R' in possible:
        errStr += ': not a register'
        err = AssemblyNameError

      elif 'V' in possible:
        errStr += ': not a recognised value'
        err = AssemblyValueError

      else: raise ErrorDetectionError('Unable to determine correct type of argument')
    else: err = AssemblyTypeError

    raise err(errStr)




  def parseCommand(self, cmd):
    '''
    Parses a command (line of assembly).
    Will try to figure out the command class, opcode, the true type and the arguments.

    :param cmd: command string (line of assembly)
    :return: cmd class, opcode, type and arguments
    '''

    cmdParts = self.parseCmdParts(cmd)
    if cmdParts:
      opcode, cmdClass, possibleTypes = self.parseOpcode(cmdParts)

      argTypes = []
      args = []
      for pos in range(1, len(cmdParts)):
        t, a = self.parseArg(opcode, cmdParts[pos])
        argTypes.append(t)
        args.append(a)

      realType = ''.join(argTypes)

      if not realType in possibleTypes: self.findError(realType, possibleTypes, args)

      args.extend([None] * (3 - len(args)))       # always return a list of length 3, so it can be unpacked to three variables
      return cmdClass, opcode, realType, args



  def postProcess(self, bf):
    """
    Clean up some minor things, e.g. unnecessary moves ('>>><<' -> '>') or STZ-sequences
    """

    bfOrg = bf[:]

    r = re.compile('((\[-\])+\s*)+')
    match = r.search(bf)
    if match:
      while 1:
        start, end = match.span()
        ws = match.group().strip('[-]')
        bf = bf[:start] + '[-]' + ws + bf[end:]
        matches = r.finditer(bf)
        for m in matches:
          if m.start() > end:
            match = m
            break
        else: break


    r = re.compile('(<+>+|>+<+)+')
    match = r.search(bf)
    while match is not None:
      s = match.group()
      nl = s.count('<')
      nr = s.count('>')

      diff = nr-nl
      if diff < 0: s = '<' * abs(diff)
      else: s = '>' * diff

      bf = bf[:match.start()] + s + bf[match.end():]
      match = r.search(bf)

    return bf


  ### parsing functions


  def compile(self, bfal, initConstants=True):
    '''
    Parses the given assembly to brainfuck commands.
    splits the assembly in lines / commands, parses them using parseCommand and compiles them to bf commands

    :param bfal: assembly input
    :param initConstants: if True, initialise constants at the start of the program
    :return: brainfuck commands
    '''


    bf = ''

    cfBlockEnds = []
    self.ALIASES = {}
    with macros.MacroContext(startPos=self.START_POS, cells=self.CELLS, temps=self.TEMPS) as mc:
      if initConstants:
        for cell, val in self.CONSTANTS:
          bf += mc.inc(cell, val)

      for cmd in bfal.split('\n'):
        try:
          parsed = self.parseCommand(cmd)
          if not parsed: continue
        
          cmdClass, opcode, cmdType, args = parsed
          if cmdClass == self.OPCODE_CLASSES.INSTRUCTION:
            arg1, arg2, arg3 = args

            if opcode == self.OPCODES.SET:
              if cmdType == 'RV': bf += mc.atCell(arg1, '[-]') + mc.setFromTo(0, int(arg2), dest=arg1)
              elif cmdType == 'RR': bf += mc.copyCell(arg1, arg2)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.STZ: bf += mc.atCell(arg1, '[-]')

            elif opcode == self.OPCODES.PUSH:
              if cmdType == 'V':
                bf += mc.atStackEnd('+>{}<'.format(mc.inc(val=int(arg1))))

              elif cmdType == 'R':
                bf += mc.doCellTimes(arg1, lambda s: s.atStackEnd('>+<<<'))
                bf += mc.atStackEnd('+')

            elif opcode == self.OPCODES.POP:
              bf += mc.set(arg1, 0)
              bf += mc.atStackEnd('<[-<') + mc.atCell(arg1, mc.inc()) + mc.atStackEnd('<]<-<<')

            elif opcode == self.OPCODES.INPUT: bf += mc.atCell(arg1, ',')
            elif opcode == self.OPCODES.OUTPUT: bf += mc.atCell(arg1, '.')


            elif opcode == self.OPCODES.INC:
              if   cmdType == 'R': bf += mc.inc(dest=arg1)
              elif cmdType == 'RV': bf += mc.inc(dest=arg1, val=int(arg2))
              elif cmdType == 'RR': bf += mc.addCell(arg1, arg2)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.DEC:
              if   cmdType == 'R': bf += mc.dec(dest=arg1)
              elif cmdType == 'RV': bf += mc.dec(dest=arg1, val=int(arg2))
              elif cmdType == 'RR': bf += mc.subCell(arg1, arg2)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.ADD:
              if   cmdType == 'RVV': bf += mc.set(arg1, int(arg2) + int(arg3))
              elif cmdType == 'RRV': bf += mc.copyCell(arg1, arg2) + mc.inc(arg1, int(arg3))
              elif cmdType == 'RRR': bf += mc.copyCell(arg1, arg2) + mc.addCell(arg1, arg3)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.SUB:
              if   cmdType == 'RVV': bf += mc.set(arg1, int(arg2) - int(arg3))
              elif cmdType == 'RRV': bf += mc.copyCell(arg1, arg2) + mc.dec(arg1, int(arg3))
              elif cmdType == 'RRR': bf += mc.copyCell(arg1, arg2) + mc.subCell(arg1, arg3)

              else: raise UnknownCmdTypeError(cmdType)

            elif opcode == self.OPCODES.MUL:
              if   cmdType == 'RVV': bf += mc.set(arg1, int(arg2) * int(arg3))
              elif cmdType == 'RRV': bf += mc.mulCell(arg1, 'RV', arg2, int(arg3))
              elif cmdType == 'RRR': bf += mc.mulCell(arg1, 'RR', arg2, arg3)

              else: raise UnknownCmdTypeError(cmdType)

            elif opcode == self.OPCODES.DIV:
              if   cmdType == 'RVV': bf += mc.set(arg1, int(arg2) // int(arg3) if int(arg3) else 0)
              elif cmdType == 'RRV':
                self.ensureCompInit = True
                bf += mc.divCell(arg1, 'RV', arg2, int(arg3))

              elif cmdType == 'RRR':
                self.ensureCompInit = True
                bf += mc.divCell(arg1, 'RR', arg2, arg3)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.TRUE:
              bf += mc.set('RC', 1)

            elif opcode == self.OPCODES.FALSE:
              bf += mc.set('RC', 0)

            elif opcode == self.OPCODES.NOT:
              self.ensureCompInit = True
              bf += mc.copyCell('CB', 'RC', destructive=True)
              bf += mc.inc('RC')
              bf += mc.ifCB(lambda s: s.dec('RC'))
              bf += mc.set('CB', 0)

            elif opcode == self.OPCODES.NOT_ZERO:
              if cmdType == 'V':
                if int(arg1) : bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'R':
                self.ensureCompInit = True
                bf += mc.set('RC', 0)
                bf += mc.addCell('CB', arg1)
                bf += mc.ifCB(lambda s: s.inc('RC'))
                bf += mc.set('CB', 0)

              else: raise UnknownCmdTypeError(cmdType)

            elif opcode == self.OPCODES.ZERO:
              if cmdType == 'V':
                if not int(arg1): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'R':
                self.ensureCompInit = True
                bf += mc.set('RC', 1)
                bf += mc.addCell('CB', arg1)
                bf += mc.ifCB(lambda s: s.dec('RC'))
                bf += mc.set('CB', 0)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.EQUAL:
              if cmdType == 'VV':
                if int(arg1) == int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.set('RC', 1)
                bf += mc.addCell('CB', arg1) + mc.dec('CB', int(arg2))
                bf += mc.ifCB(lambda s: s.dec('RC'))
                bf += mc.set('CB', 0)

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.set('RC', 1)

                if arg1 != arg2: # if registers are equal, their values are -> EQ is true
                  bf += mc.addCell('CB', arg1) + mc.subCell('CB', arg2)
                  bf += mc.ifCB(lambda s: s.dec('RC'))
                  bf += mc.set('CB', 0)


            elif opcode == self.OPCODES.NOT_EQUAL:
              if cmdType == 'VV':
                if int(arg1) != int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.set('RC', 0)
                bf += mc.addCell('CB', arg1) + mc.dec('CB', int(arg2))
                bf += mc.ifCB(lambda s: s.inc('RC'))
                bf += mc.set('CB', 0)

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.set('RC', 0)

                if arg1 != arg2: # if registers are equal, their values are -> NEQ is false
                  bf += mc.addCell('CB', arg1) + mc.subCell('CB', arg2)
                  bf += mc.ifCB(lambda s: s.inc('RC'))
                  bf += mc.set('CB', 0)


            elif opcode == self.OPCODES.GREATER:
              if cmdType == 'VV':
                if int(arg1) > int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.comparison('RV', arg1, int(arg2), 'GT')

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.comparison('RR', arg1, arg2, 'GT')

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.GREATER_EQUAL:
              if cmdType == 'VV':
                if int(arg1) >= int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.comparison('RV', arg1, int(arg2), 'GE')

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.comparison('RR', arg1, arg2, 'GE')

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.LESS:
              if cmdType == 'VV':
                if int(arg1) < int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.comparison('RV', arg1, int(arg2), 'LT')

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.comparison('RR', arg1, arg2, 'LT')

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.LESS_EQUAL:
              if cmdType == 'VV':
                if int(arg1) <= int(arg2): bf += mc.set('RC', 1)
                else: bf += mc.set('RC', 0)

              elif cmdType == 'RV':
                self.ensureCompInit = True
                bf += mc.comparison('RV', arg1, int(arg2), 'LE')

              elif cmdType == 'RR':
                self.ensureCompInit = True
                bf += mc.comparison('RR', arg1, arg2, 'LE')

              else: raise UnknownCmdTypeError(cmdType)

            else: raise UnknownOpcodeError(opcode)


          elif cmdClass == self.OPCODE_CLASSES.CONTROLFLOW_START:
            if opcode in (self.OPCODES.LOOP, self.OPCODES.IF):
              bf += mc.moveToCell('RC')
              bf += '['

              if opcode == self.OPCODES.LOOP: cfBlockEnds.append(self.OPCODES.END_LOOP)
              elif opcode == self.OPCODES.IF: cfBlockEnds.append(self.OPCODES.END_IF)

            else: raise UnknownOpcodeError(opcode)


          elif cmdClass == self.OPCODE_CLASSES.CONTROLFLOW_END:
            blockEnd = cfBlockEnds.pop()
            if blockEnd != opcode: SyntaxError('Unexpected control flow block end')

            if opcode == self.OPCODES.END_LOOP:
              bf += mc.moveToCell('RC') + ']'

            elif opcode == self.OPCODES.END_IF:
              bf += mc.set('RC', 0) + ']'

            else: raise UnknownOpcodeError(opcode)

          elif cmdClass == self.OPCODE_CLASSES.SPECIAL:
            arg1, arg2, arg3 = args

            if opcode == self.OPCODES.ALIAS: self.ALIASES[arg1] = arg2
            elif opcode == self.OPCODES.PRINT: bf += mc.moveToCell(mc.getClosestTemp()) + mc.printText(arg1)

            else: raise UnknownOpcodeError(opcode)


          else: raise UnknownCmdClassError(cmdClass)

          if bf and not bf[-1] == '\n': bf += '\n'

        except (AssemblyError, InternalError, Exception) as err:
          if isinstance(err, AssemblyError):
            msg = 'Error while parsing the command "{}":\n\t{}: {}'.format(cmd, err.name, err)
            print(msg)
            sys.exit(-1)

          elif isinstance(err, InternalError): msg = 'Bad news, an internal error occured'
          else: msg = 'Very bad news, a runtime error occured'

          msg += ' while parsing the command "{}":\n\t'.format(cmd)
          print(msg)
          raise err

    return self.postProcess(bf)



  def _ensureCompInit(self, bf):
    """Ensures that the compare section is initialised"""




