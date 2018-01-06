'''
Parser for the Brainfuck Assembly Language (BFAL)

The Parser is the main class to convert BFAL code to brainfuck.


Marius Lambacher, 2017
'''

import sys

from ..util import *
from . import makros
from . import memoryLayout
from . import opcodes
from .errors import *



class Parser:
  def __init__(self):
    ###  aliases as defined with the 'ALIAS' command
    self.ALIASES = {}

    self.OPCODE_CLASSES = opcodes.OPCODE_CLASSES
    self.OPCODES = opcodes.OPCODES
    self.OPCODE_IDENTIFIERS = opcodes.OPCODE_IDENTIFIERS
    self.OPCODE_TYPES = opcodes.OPCODE_TYPES

    self.REGISTERS = memoryLayout.REGISTERS
    self.TEMPS = memoryLayout.TEMPS
    self.CELLS = memoryLayout.CELLS
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





  ### parsing functions


  def compile(self, bfal):
    '''
    Parses the given assembly to brainfuck commands.
    splits the assembly in lines / commands, parses them using parseCommand and compiles them to bf commands

    :param bfal: assembly input
    :return: brainfuck commands
    '''

    bf = ''

    cfBlockEnds = []
    self.ALIASES = {}
    with makros.MakroContext(self.START_POS) as mc:
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
              if   cmdType == 'RRV': bf += mc.copyCell(arg1, arg2) + mc.inc(arg1, int(arg3))
              elif cmdType == 'RRR': bf += mc.copyCell(arg1, arg2) + mc.addCell(arg1, arg3)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.SUB:
              if cmdType == 'RRV': bf += mc.copyCell(arg1, arg2) + mc.dec(arg1, int(arg3))
              elif cmdType == 'RRR': bf += mc.copyCell(arg1, arg2) + mc.subCell(arg1, arg3)

              else: raise UnknownCmdTypeError(cmdType)


            elif opcode == self.OPCODES.TRUE:
              bf += mc.set('RC', 1)

            elif opcode == self.OPCODES.FALSE:
              bf += mc.set('RC', 0)

            elif opcode == self.OPCODES.NOT_ZERO:
              if cmdType == 'V':
                bf += mc.set('RC', 0)
                if int(arg1):
                  bf += '+'

              elif cmdType == 'R':
                bf += mc.set('RC', 0)
                bf += mc.addCell('RC', arg1)

              else: raise UnknownCmdTypeError(cmdType)
              bf += mc.moveToCell('RC')

            elif opcode == self.OPCODES.NOT_EQUAL:
              if cmdType == 'VV':
                bf += mc.set('RC', 0)
                if int(arg1) != int(arg2):
                  bf += '+'

              elif cmdType == 'RV':
                bf += mc.set('RC', 0)
                bf += mc.addCell('RC', arg1) + mc.dec('RC', int(arg2))

              elif cmdType == 'RR':
                bf += mc.set('RC', 0)
                if arg1 != arg2: bf += mc.addCell('RC', arg1) + mc.subCell('RC', arg2)    # if registers are equal, their values are -> NEQ is false

            elif opcode == self.OPCODES.GREATER:
              if cmdType == 'VV':
                bf += mc.set('RC', 0)
                if int(arg1) > int(arg2):
                  bf += '+'

              elif cmdType == 'RV':
                bf += mc.set('RC', 0)
                bf += mc.addCell('RC', arg1) + mc.dec('RC', int(arg2))

              elif cmdType == 'RR':
                bf += mc.set('RC', 0)
                if arg1 != arg2:     # if registers are equal, their values are -> GT is false
                  tx = mc.getClosestTemp('RC')
                  ty = mc.getClosestTemp('RC', omit=[tx,])
                  tflag = mc.getClosestTemp('RC', omit=[tx, ty])
                  trest = mc.getClosestTemp('RC', omit=[tx, ty, tflag])

                  bf += mc.moveToCell(arg1) + '['
                  bf += mc.inc(tflag)
                  bf += mc.moveToCell(arg2) + mc.loop(mc.dec()+ mc.set(tflag, 0) + mc.inc(trest) + mc.moveToCell(arg2))
                  bf += mc.addCell(arg2, trest, destructive=True)
                  bf += mc.addCell('RC', tflag, destructive=True)
                  bf += mc.dec(arg2) + mc.inc(tx) + mc.dec(arg1) + ']'
                  bf +=  mc.moveToCell(tx) + mc.loop(mc.dec()+ mc.inc(arg1) + mc.inc(arg2) + mc.moveToCell(tx))
                  bf += mc.moveToCell('RC')


              else: raise UnknownCmdTypeError(cmdType)
              bf += mc.moveToCell('RC')

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
            elif opcode == self.OPCODES.PRINT: bf += mc.atTemp(mc.printText(arg1))

            else: raise UnknownOpcodeError(opcode)


          else: raise UnknownCmdClassError(cmdClass)

          if bf and not bf[-1] == '\n': bf += '\n'

        except (AssemblyError, InternalError, Exception) as err:
          msg = ''
          if isinstance(err, AssemblyError):
            msg = 'Error while parsing the command "{}":\n\t{}: {}'.format(cmd, err.name, err)
            print(msg)
            sys.exit(-1)

          elif isinstance(err, InternalError): msg = 'Bad news, an internal error occured'
          else: msg = 'Very bad news, a runtime error occured'

          msg += ' while parsing the command "{}":\n\t'.format(cmd)
          print(msg)
          raise err


    return bf
