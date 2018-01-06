'''
Opcode definitions for the Brainfuck Assembly Language (BFAL)

This file defines the opcodes used by the assembly language.
An opcode consists of the following:
  - an integer entry in the OPCODES enum; loosely sorted by type
  - an identifier defined in the OPCODE_IDENTIFIERS dict; used for for calling it in the assembly code
  - a type definition in OPCODE_TYPES; consisting of the corresponding opcode class and a tuple of possible argument types

For a condition, the definition is rather similar.

The argument types are the following:
  - 'R': a register
  - 'V': a value (int, with literal)
  - 'T': text

Therefore, the opcode 'FOO' of type ('RR', 'RRV') could be called in one of the following ways:
  - FOO R1 2
  - FOO R2 R1 0

  - but not: FOO R2 1 R0 (this would be of type 'RVR')



Marius Lambacher, 2017
'''


from enum import Enum

### opcodes

class OPCODE_CLASSES(Enum):
  INSTRUCTION = 1
  CONTROLFLOW_START = 2
  CONTROLFLOW_END = 3
  SPECIAL = 4


class OPCODES(Enum):
  SET = 100
  STZ = 101

  INC = 110
  DEC = 111
  ADD = 112
  SUB = 113

  TRUE = 120
  FALSE = 121
  NOT_ZERO = 122
  NOT_EQUAL = 123
  GREATER = 124
  LESSEQUAL = 125

  INPUT = 130
  OUTPUT = 131

  LOOP = 200
  IF = 201

  END_LOOP = 300
  END_IF = 301

  ALIAS = 400
  PRINT = 401


OPCODE_IDENTIFIERS = {
  'SET': OPCODES.SET,
  'STZ': OPCODES.STZ,

  'INC': OPCODES.INC,
  'DEC': OPCODES.DEC,
  'ADD': OPCODES.ADD,
  'SUB': OPCODES.SUB,

  'TRUE': OPCODES.TRUE,
  'FALSE': OPCODES.FALSE,
  'NZR': OPCODES.NOT_ZERO,
  'NEQ': OPCODES.NOT_EQUAL,
  'GT': OPCODES.GREATER,
  'LE': OPCODES.LESSEQUAL,

  'INP': OPCODES.INPUT,
  'OUT': OPCODES.OUTPUT,

  'LOOP': OPCODES.LOOP,
  'IF': OPCODES.IF,

  'ENDLOOP': OPCODES.END_LOOP,
  'ENDIF': OPCODES.END_IF,

  'ALIAS': OPCODES.ALIAS,
  'PRT': OPCODES.PRINT
}

OPCODE_TYPES = {
  OPCODES.SET: (OPCODE_CLASSES.INSTRUCTION, ('RV', 'RR')),
  OPCODES.STZ: (OPCODE_CLASSES.INSTRUCTION, ('R',)),

  OPCODES.INC: (OPCODE_CLASSES.INSTRUCTION, ('R', 'RV', 'RR')),
  OPCODES.DEC: (OPCODE_CLASSES.INSTRUCTION, ('R', 'RV', 'RR')),
  OPCODES.ADD: (OPCODE_CLASSES.INSTRUCTION, ('RRV', 'RRR')),
  OPCODES.SUB: (OPCODE_CLASSES.INSTRUCTION, ('RRV', 'RRR')),

  OPCODES.TRUE: (OPCODE_CLASSES.INSTRUCTION, ('',)),
  OPCODES.FALSE: (OPCODE_CLASSES.INSTRUCTION, ('',)),
  OPCODES.NOT_ZERO: (OPCODE_CLASSES.INSTRUCTION, ('V', 'R')),
  OPCODES.NOT_EQUAL: (OPCODE_CLASSES.INSTRUCTION, ('VV', 'RV', 'RR')),
  OPCODES.GREATER: (OPCODE_CLASSES.INSTRUCTION, ('VV', 'RV', 'RR')),
  OPCODES.LESSEQUAL: (OPCODE_CLASSES.INSTRUCTION, ('VV', 'RV', 'RR')),

  OPCODES.INPUT: (OPCODE_CLASSES.INSTRUCTION, ('R',)),
  OPCODES.OUTPUT: (OPCODE_CLASSES.INSTRUCTION, ('R',)),

  OPCODES.LOOP: (OPCODE_CLASSES.CONTROLFLOW_START, ('',)),
  OPCODES.IF: (OPCODE_CLASSES.CONTROLFLOW_START, ('',)),

  OPCODES.END_LOOP: (OPCODE_CLASSES.CONTROLFLOW_END, ('',)),
  OPCODES.END_IF: (OPCODE_CLASSES.CONTROLFLOW_END, ('',)),

  OPCODES.ALIAS: (OPCODE_CLASSES.SPECIAL, ('TV', 'TR')),
  OPCODES.PRINT: (OPCODE_CLASSES.SPECIAL, ('T',))
}
