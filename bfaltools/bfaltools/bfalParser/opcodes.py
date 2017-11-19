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
  - 'C': a condition (for control flow)
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
  INPUT = 110
  OUTPUT = 111
  INC = 120
  DEC = 121
  ADD = 130
  SUB = 131

  WHILE = 200
  IF = 201

  END_WHILE = 300
  END_IF = 301

  ALIAS = 400
  PRINT = 401


OPCODE_IDENTIFIERS = {
  'SET': OPCODES.SET,
  'STZ': OPCODES.STZ,
  'INP': OPCODES.INPUT,
  'OUT': OPCODES.OUTPUT,
  'INC': OPCODES.INC,
  'DEC': OPCODES.DEC,
  'ADD': OPCODES.ADD,
  'SUB': OPCODES.SUB,

  'WHILE': OPCODES.WHILE,
  'IF': OPCODES.IF,

  'ENDWHILE': OPCODES.END_WHILE,
  'ENDIF': OPCODES.END_IF,

  'ALIAS': OPCODES.ALIAS,
  'PRT': OPCODES.PRINT
}

OPCODE_TYPES = {
  OPCODES.SET: (OPCODE_CLASSES.INSTRUCTION, ('RV', 'RR')),
  OPCODES.STZ: (OPCODE_CLASSES.INSTRUCTION, ('R',)),
  OPCODES.INPUT: (OPCODE_CLASSES.INSTRUCTION, ('R',)),
  OPCODES.OUTPUT: (OPCODE_CLASSES.INSTRUCTION, ('R',)),
  OPCODES.INC: (OPCODE_CLASSES.INSTRUCTION, ('R', 'RV', 'RR')),
  OPCODES.DEC: (OPCODE_CLASSES.INSTRUCTION, ('R', 'RV', 'RR')),
  OPCODES.ADD: (OPCODE_CLASSES.INSTRUCTION, ('RRV', 'RRR')),
  OPCODES.SUB: (OPCODE_CLASSES.INSTRUCTION, ('RRV', 'RRR')),

  OPCODES.WHILE: (OPCODE_CLASSES.CONTROLFLOW_START, ('C',)),
  OPCODES.IF: (OPCODE_CLASSES.CONTROLFLOW_START, ('C',)),

  OPCODES.END_WHILE: (OPCODE_CLASSES.CONTROLFLOW_END, (OPCODES.WHILE,)),
  OPCODES.END_IF: (OPCODE_CLASSES.CONTROLFLOW_END, (OPCODES.IF,)),

  OPCODES.ALIAS: (OPCODE_CLASSES.SPECIAL, ('TV', 'TR')),
  OPCODES.PRINT: (OPCODE_CLASSES.SPECIAL, ('T',))
}


class CONDITIONS(Enum):
  NOT_ZERO = 100
  NOT_EQUAL = 101

CONDITION_IDENTIFIERS = {
  'NZR': CONDITIONS.NOT_ZERO,
  'NEQ': CONDITIONS.NOT_EQUAL
}

CONDITION_TYPES = {
  CONDITIONS.NOT_ZERO: ('R',),
  CONDITIONS.NOT_EQUAL: ('RV', 'RR')
}