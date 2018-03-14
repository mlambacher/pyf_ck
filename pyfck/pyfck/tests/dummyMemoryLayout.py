'''
Dummy memory layout for testing

Marius Lambacher, 2017
'''


RESERVED = []
REGISTERS = ['R0', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7']
TEMPS = ['T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']

CELLS = []
CELLS += RESERVED
for r, t in zip(REGISTERS, TEMPS):
  CELLS.extend((r, t))


### starting position of memory pointer
START_POS = 0