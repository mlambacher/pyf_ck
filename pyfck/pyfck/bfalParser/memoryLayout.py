'''
Memory layout for the Brainfuck Assembly Language (BFAL)

This file defines the memory on which the assembly operates:
  - REGISTERS : cells which function as registers
  - TEMPS     : cells which are internally used for temporary storage (for algorithms)
  - RESERVED  : other cells which are reserved for the system

The final layout is determined by the CELLS list; corresponding to the memory as seen by the brainfuck interpreter

This file also defines the initial value for the memory pointer - usually 0 (first cell)

Marius Lambacher, 2017
'''


COMPARISON = ['C0', 'C1', 'C2', 'CB', 'CA']
REGISTERS = ['RC', 'R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
TEMPS = ['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
STACK = ['STACK', 'STACK0']

CONSTANTS = (('C1', 1),)

CELLS = []
CELLS += COMPARISON
CELLS.append(REGISTERS[0])
for r, t in zip(REGISTERS[1:], TEMPS):
  CELLS.append(r)
  CELLS.append(t)

CELLS += STACK


### starting position of memory pointer
START_POS = 0