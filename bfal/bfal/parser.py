'''
Parser for the Brainfuck Assembly Language (BFAL)

The Parser is the main class to convert BFAL code to brainfuck.



Marius Lambacher, 2017
'''

from .memoryLayout import *
from .opcodes import *
import bfal.makros as makros

import sys


def litStrToInt(s):
  '''
  String to int conversion. Accepts literals '0b' for binary and '0x' for hexadecimal (and none for decimal).

  :param s: string to convert
  :return: converted int
  '''

  try:
    if s[:2] == '0b':
      i = int(s[2:], 2)
    elif s[:2] == '0x':
      i = int(s[2:], 16)
    else:
      i = int(s)

    return i

  except ValueError:
    raise ValueError('Cannot parse to int: {}'.format(s))




class Parser:
  def __init__(self):
    ###  aliases as defined with the 'ALIAS' command
    self.ALIASES = {}

    makros.CUR_POS = START_POS


  def parseCmdParts(self, cmd):
    '''
    Splits a line of assembly into its parts.
    Splitting occurs at whitespace; though blocks enclosed by quotes wil be treated as one part.

    :param cmd: command to split (string)
    :return: list of cmd parts
    '''

    cmd = cmd.split('//')[0]
    if cmd.count('"') % 2 != 0: raise SyntaxError('Quotations must be of even number')
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

    if opcodeId not in OPCODE_IDENTIFIERS: raise NameError('Unknown opcode {}'.format(opcodeId))

    opcode = OPCODE_IDENTIFIERS[opcodeId]
    cmdClass, cmdType = OPCODE_TYPES[opcode]
    return opcode, cmdClass, cmdType




  def parseArg(self, opcode, cmdParts, position):
    '''
    Tries to parse an argument for cmdParts
    If the opcode is not the alias opcode, the aliases will be applied here.
    The function will try to determine the type of argument, distinguishing between conditions ('C'),
    registers ('R'), (int-)values ('V') and text ('T').
    Default is text.

    :param opcode: opcode of current command; used for alias
    :param cmdParts: list of cmd parts
    :param position: position of argument
    :return: type of argument, argument
    '''

    arg = cmdParts[position]

    if opcode != OPCODES.ALIAS:                       # don't apply the aliases in the alias command, or else they can't be overwritten
      if arg in self.ALIASES.keys(): arg = self.ALIASES[arg]

    if arg in CONDITION_IDENTIFIERS:
      argType = 'C'
      arg = CONDITION_IDENTIFIERS[arg]

    elif arg in REGISTERS:
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
      if len(possibleLengths) == 1: raise TypeError('Wrong number of arguments ({}), must be {}'.format(length, possibleLengths[0]))
      else: raise TypeError('Wrong number of arguments ({}), must be in {}'.format(length, sorted(possibleLengths)))
    possibleTypes = [t for t in possibleTypes if len(t)==length]


    for pos in range(length):
      possible = [t[pos] for t in possibleTypes]
      if not type[pos] in possible:
        break

    else: raise RuntimeError('Something went wrong, unable to detect error in arguments')


    errStr = 'Invalid argument {}: \'{}\''.format(pos+1, args[pos])

    if len(possible) == 1:
      if possible == 'R':
        errStr += ': not a register'
        err = NameError

      elif possible == 'V':
        errStr += ': not a recognised value'
        err = ValueError

      elif possible == 'C':
        errStr += ': not a recognised condition'
        err = NameError

      else: err = TypeError
    else: err = TypeError

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
      for pos in range(len(cmdParts)-1):
        t, a = self.parseArg(opcode, cmdParts, pos+1)
        argTypes.append(t)
        args.append(a)

      realType = ''.join(argTypes)

      if cmdClass != OPCODE_CLASSES.CONTROLFLOW_END:
        for t in possibleTypes:
          if t == realType: break
          elif t == 'C' and realType[0] == 'C':
            if realType[1:] in CONDITION_TYPES[args[0]]: break

        else: self.findError(realType, possibleTypes, args)

      else:
        if realType != '': raise SyntaxError('Controlflow end identifier must not be called with arguments')
        realType = possibleTypes

      args.extend([None] * (3 - len(args)))       # always return a tuple of length 3, so it can be unpacked to three variables
      return cmdClass, opcode, realType, args



  ### low level assembly macros




  def evalCondition(self, cmdType, condition, src1, src2, dest=None, forceTemp=True):
    '''
    Evaluate the given condition; if true, the head will read nonzero, if false, zero.
    If the dest cell is given, the condition will be evaluated there
      - this is needed for loops etc, where the condition needs to be evaluated at the same cell before entry and inside the loop.
    If forceTemp is False, the condition can be evaluated at a non-temp cell (e.g. nonzero can be checked by just moving to the corresponding cell)

    :param cmdType: type of command
    :param condition: condition to evaluate
    :param src1: first source argument (or None)
    :param src2: second source argument (or None)
    :param dest: if given, the condition will be evaluated here
    :param forceTemp: if False, the condition can be evaluated at a non-temp cell
    :return: cell where the condition is evaluated, lla commands
    '''

    if condition == CONDITIONS.NOT_ZERO:
      if cmdType == 'CR':
        if forceTemp or (dest and dest != src1):
          if not dest: dest = makros.getClosestTemp(cell=src1)
          cmds = makros.addCell(dest, src1) + makros.moveToCell(dest)   #addCell('CD', src1) + moveToCell('CD')

        else:
          dest = src1
          cmds = makros.moveToCell(dest)

      else: raise RuntimeError('Unknown type: {}'.format(cmdType))

    elif condition == CONDITIONS.NOT_EQUAL:
      if cmdType == 'CRV':
        if not dest: dest = makros.getClosestTemp(cell=src1)
        cmds = makros.addCell(dest, src1) + makros.dec(dest, int(src2)) + makros.moveToCell(dest)

      elif cmdType == 'CRR':
        if not dest: dest = makros.getClosestTemp(cell=src1, directionCell=src2)
        cmds = makros.addCell(dest, src1) + makros.subCell(dest, src2) + makros.moveToCell(dest)

      else: raise RuntimeError('Unknown type: {}'.format(cmdType))

    else: raise RuntimeError('Unknown condition: {}'.format(condition))

    return dest, cmds



  ### parsing functions


  def compile(self, bfal):
    '''
    Parses the given assembly to brainfuck commands.
    splits the assembly in lines / commands, parses them using parseCommand and compiles them to lla commands

    :param bfal: assembly input
    :return: brainfuck commands
    '''

    bf = ''

    cfBlockEnds = []
    for cmd in bfal.split('\n'):
      try:
        parsed = self.parseCommand(cmd)
        if not parsed: continue

        cmdClass, opcode, cmdType, args = parsed
        if cmdClass == OPCODE_CLASSES.INSTRUCTION:
          dest, src1, src2 = args

          if opcode == OPCODES.SET:
            if cmdType == 'RV': bf += makros.atCell(dest, '[-]') + makros.setFromTo(0, int(src1), dest=dest)
            elif cmdType == 'RR': bf += makros.copyCell(dest, src1)

            else: raise RuntimeError('Unknown type: {}'.format(cmdType))


          elif opcode == OPCODES.STZ: bf += makros.atCell(dest, '[-]')

          elif opcode == OPCODES.INPUT: bf += makros.atCell(dest, ',')
          elif opcode == OPCODES.OUTPUT: bf += makros.atCell(dest, '.')


          elif opcode == OPCODES.INC:
            if   cmdType == 'R': bf += makros.inc(dest=dest)
            elif cmdType == 'RV': bf += makros.inc(dest=dest, val=int(src1))
            elif cmdType == 'RR': bf += makros.addCell(dest, src1)

            else: raise RuntimeError('Unknown type: {}'.format(cmdType))


          elif opcode == OPCODES.DEC:
            if   cmdType == 'R': bf += makros.dec(dest=dest)
            elif cmdType == 'RV': bf += makros.dec(dest=dest, val=src1)
            elif cmdType == 'RR': bf += makros.addCell(dest, src1)

            else: raise RuntimeError('Unknown type: {}'.format(cmdType))


          elif opcode == OPCODES.ADD:
            if   cmdType == 'RRV': bf += makros.copyCell(dest, src1) + makros.inc(dest, int(src2))
            elif cmdType == 'RRR': bf += makros.copyCell(dest, src1) + makros.addCell(dest, src2)

            else: raise RuntimeError('Unknown type: {}'.format(cmdType))


          elif opcode == OPCODES.SUB:
            if cmdType == 'RRV': bf += makros.copyCell(dest, src1) + makros.dec(dest, int(src2))
            elif cmdType == 'RRR': bf += makros.copyCell(dest, src1) + makros.subCell(dest, src2)

            else: raise RuntimeError('Unknown type: {}'.format(cmdType))

          else: raise RuntimeError('Unknown opcode: {}'.format(opcode))


        elif cmdClass == OPCODE_CLASSES.CONTROLFLOW_START:
          condition, src1, src2 = args

          if opcode == OPCODES.WHILE:
            dest, cmds = self.evalCondition(cmdType, condition, src1, src2, forceTemp=False)
            bf += cmds + '['
            if dest in TEMPS: bf += '[-]'

            llaEnd = lambda args: self.evalCondition(*args[:-1], dest=args[-1], forceTemp=False)[1] + ']'

          elif opcode == OPCODES.IF:
            dest, cmds = self.evalCondition(cmdType, condition, src1, src2)
            bf += cmds + '[[-]'
            llaEnd = lambda args: makros.moveToCell(args[-1]) + ']'

          else: raise RuntimeError('Unknown opcode: {}'.format(opcode))

          args = [cmdType, condition, src1, src2, dest]
          cfBlockEnds.append((opcode, llaEnd, args))


        elif cmdClass == OPCODE_CLASSES.CONTROLFLOW_END:
          ends = cmdType

          blockEnd = cfBlockEnds.pop()
          if not blockEnd[0] in ends: raise SyntaxError('Unexpected control flow block end')

          bf += blockEnd[1](blockEnd[2])


        elif cmdClass == OPCODE_CLASSES.SPECIAL:
          arg1, arg2, arg3 = args

          if opcode == OPCODES.ALIAS: self.ALIASES[arg1] = arg2
          elif opcode == OPCODES.PRINT: bf += makros.atTemp(makros.printText(arg1))

          else: raise RuntimeError('Unknown opcode: {}'.format(opcode))



        else: raise RuntimeError('Unknown command class {}'.format(cmdClass))

        if bf and not bf[-1] == '\n': bf += '\n'


      except (NameError, ValueError, IndexError, TypeError, SyntaxError, RuntimeError) as err:
        print('Error while parsing command "{}":\n\t{}'.format(cmd, err))
        sys.exit()

    return bf
